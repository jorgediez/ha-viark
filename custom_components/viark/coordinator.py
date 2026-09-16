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
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CHANNEL_CACHE_REFRESH_SECONDS,
    DOMAIN,
    REFRESH_COOLDOWN_SECONDS,
    SCAN_INTERVAL_SECONDS,
)
from .protocol import (
    NOTIFY_CHANNEL_LIST_CHANGED,
    ViarkClient,
    ViarkError,
)

_LOGGER = logging.getLogger(__name__)

#: Upper bound on re-reads within one refresh (see _async_update_data).
MAX_FETCH_PASSES = 3


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
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=REFRESH_COOLDOWN_SECONDS, immediate=True
            ),
        )
        self.client = client
        client.on_notification = self._handle_notification
        self._channels: list[dict[str, Any]] = []
        self._channels_fetched_at: float = 0.0
        self._channel_count: int | None = None
        # Set by every push, cleared when a fetch pass starts. Still set when the
        # pass ends means the state changed under it -- see _async_update_data.
        self._push_seen = False
        # The last channel request 3 reported, kept for when it is refused.
        self._last_reported: dict[str, Any] | None = None

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
        self._push_seen = True
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> ViarkState:
        """Fetch the state, re-reading if a push arrived while it was being read.

        Home Assistant drops a refresh request made while a refresh is running
        rather than queuing it, so a push landing mid-fetch would otherwise be
        lost: the pass may already have read the old channel, and nothing would
        correct it until the next push or poll. Fast zapping hits this, since the
        receiver sends a second 2001 about a second into each change. Re-reading
        inside the same refresh avoids racing the lock HA still holds.

        The pass limit keeps a receiver that never stops pushing from pinning the
        refresh. Hitting it with a push still unread schedules a follow-up for
        after the cooldown: by then this refresh has released the lock, so the
        request is queued or run rather than dropped.
        """
        for attempt in range(1, MAX_FETCH_PASSES + 1):
            self._push_seen = False
            state = await self._async_fetch()
            if not self._push_seen:
                return state
            if attempt < MAX_FETCH_PASSES:
                _LOGGER.debug("receiver pushed during a fetch; reading again")

        _LOGGER.debug(
            "receiver still pushing after %s reads; refreshing again shortly",
            MAX_FETCH_PASSES,
        )
        async_call_later(self.hass, REFRESH_COOLDOWN_SECONDS, self._async_follow_up)
        return state

    @callback
    def _async_follow_up(self, _now: Any) -> None:
        """Request the refresh a capped update could not make itself."""
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_fetch(self) -> ViarkState:
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
        try:
            program_id = await self.client.playing_program_id(strict=True)
        except ViarkError:
            # The receiver refuses request 3 (status 5) mid-zap. Keep what it
            # last reported: the fallback below reads the cached list's Playing
            # flag, which can be an hour old and name a channel long since left.
            # The push that follows the change brings the real answer. With no
            # earlier answer this firmware may lack request 3, so fall through.
            if self._last_reported is not None:
                return self._last_reported
        else:
            if program_id:
                self._last_reported = self._match(channels, program_id)
                return self._last_reported

        # Fall back to the per-record flag, which some firmwares set instead.
        return next((c for c in channels if c.get("Playing")), None)

    @staticmethod
    def _match(channels: list[dict[str, Any]], program_id: str) -> dict[str, Any]:
        match = next((c for c in channels if c.get("ServiceID") == program_id), None)
        if match:
            return match
        # Known to be playing, but not in the cached list (e.g. a radio channel
        # while the TV list is cached). Report what little we know.
        return {"ServiceID": program_id}
