"""State coordination for the Viark receiver.

The receiver pushes a notification whenever its state changes, so this coordinator
is push-driven: a poll is only a backstop against a missed notification.

Cost matters here. The channel list runs to a thousand records, so it is cached and
refreshed only when the receiver says it changed (2002) or the cache ages out. The
tuned channel comes from request 3, which returns just the playing ProgramId, so
identifying the current channel costs one cheap request rather than a full sweep.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CHANNEL_CACHE_REFRESH_SECONDS, DOMAIN, SCAN_INTERVAL_SECONDS
from .protocol import (
    NOTIFY_CHANNEL_LIST_CHANGED,
    ViarkClient,
    ViarkError,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class ViarkState:
    """Everything the entities need for one update cycle."""

    info: dict[str, Any] = field(default_factory=dict)
    channels: list[dict[str, Any]] = field(default_factory=list)
    current: dict[str, Any] | None = None
    muted: bool = False

    @property
    def available(self) -> bool:
        return bool(self.info)

    @property
    def powered_on(self) -> bool:
        # PowerMode 1 == running; standby reports a different value.
        return self.info.get("PowerMode") in (None, 1)

    @property
    def channel_count(self) -> int:
        return len(self.channels)


class ViarkCoordinator(DataUpdateCoordinator[ViarkState]):
    """Fetches and caches receiver state."""

    def __init__(self, hass: HomeAssistant, client: ViarkClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        client.on_notification = self._handle_notification
        self._channels: list[dict[str, Any]] = []
        self._channels_fetched_at: float = 0.0
        self._channel_count: int | None = None

    @callback
    def _handle_notification(self, notification: int) -> None:
        """React to a receiver push by refreshing.

        Called from the protocol read loop, which already runs on the event loop.
        The coordinator debounces, so bursts of notifications (a keypress emits
        several) collapse into one refresh.
        """
        if notification == NOTIFY_CHANNEL_LIST_CHANGED:
            # Force the cached list to be re-read on the next update.
            self._channels = []
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> ViarkState:
        try:
            info = await self.client.state()
            if not info:
                raise UpdateFailed("receiver returned no state")

            channels = await self._async_channels(int(info.get("ChannelNum", 0)))
            current = await self._async_current(channels)

            muted = await self.client.mute_state()
            if muted is None:
                muted = bool(info.get("MuteState"))
        except ViarkError as exc:
            raise UpdateFailed(f"error talking to receiver: {exc}") from exc

        return ViarkState(info=info, channels=channels, current=current, muted=muted)

    async def _async_channels(self, count: int) -> list[dict[str, Any]]:
        stale = (time.monotonic() - self._channels_fetched_at) > CHANNEL_CACHE_REFRESH_SECONDS
        if self._channels and count == self._channel_count and not stale:
            return self._channels

        _LOGGER.debug("refreshing Viark channel list (%s channels)", count)
        self._channels = await self.client.channels(0, max(count - 1, 0))
        self._channels_fetched_at = time.monotonic()
        self._channel_count = count
        return self._channels

    async def _async_current(
        self, channels: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Resolve the playing channel from the ProgramId request 3 returns."""
        program_id = await self.client.playing_program_id()
        if program_id:
            match = next(
                (c for c in channels if c.get("ServiceID") == program_id), None
            )
            if match:
                return match
            # Known to be playing, but not in the cached list (e.g. a radio
            # channel while the TV list is cached). Report what little we know.
            return {"ServiceID": program_id}

        # Fall back to the per-record flag, which some firmwares set instead.
        return next((c for c in channels if c.get("Playing")), None)
