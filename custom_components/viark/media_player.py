"""Media player entity for the Viark satellite receiver."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ViarkConfigEntry
from .channels import build_labels, format_label, label_width, resolve
from .const import (
    ATTR_KEY,
    ATTR_REPEAT,
    DOMAIN,
    KEY_DOWN,
    KEY_MUTE,
    KEY_UP,
    KEY_VOLUME_DOWN,
    KEY_VOLUME_UP,
    SERVICE_SEND_KEY,
)
from .coordinator import ViarkCoordinator, ViarkState
from .protocol import ViarkError

_LOGGER = logging.getLogger(__name__)

#: The receiver drops keys sent back to back without a gap.
KEY_INTERVAL = 0.45


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ViarkConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Viark media player."""
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SEND_KEY,
        {
            vol.Required(ATTR_KEY): cv.string,
            vol.Optional(ATTR_REPEAT, default=1): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=50)
            ),
        },
        "async_send_key",
    )
    async_add_entities([ViarkMediaPlayer(entry.runtime_data, entry)])


class ViarkMediaPlayer(CoordinatorEntity[ViarkCoordinator], MediaPlayerEntity):
    """Represents the receiver as a TV-style media player."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = (
        MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: ViarkCoordinator, entry: ViarkConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = entry.entry_id
        login = coordinator.client.info
        info = coordinator.data.info if coordinator.data else {}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Viark",
            model=info.get("ProductName") or login.get("model") or "Viark receiver",
            name=info.get("ProductName") or login.get("model") or "Viark receiver",
            sw_version=info.get("SoftwareVersion"),
            serial_number=info.get("SerialNumber") or login.get("serial"),
        )

    @property
    def _state(self) -> ViarkState:
        return self.coordinator.data

    @property
    def available(self) -> bool:
        return super().available and self._state is not None and self._state.available

    @property
    def state(self) -> MediaPlayerState:
        if not self._state.powered_on:
            return MediaPlayerState.STANDBY
        if self._state.current is None:
            return MediaPlayerState.IDLE
        return MediaPlayerState.PLAYING

    @property
    def is_volume_muted(self) -> bool:
        return self._state.muted

    @property
    def source(self) -> str | None:
        """The current channel, labelled to match an entry in `source_list`."""
        current = self._state.current
        if not current:
            return None
        # A channel playing but absent from the cached list arrives as a stub
        # with only a ServiceID, which cannot be labelled; report no source
        # rather than an empty string that matches nothing in source_list.
        return format_label(current, label_width(len(self._state.channels))) or None

    @property
    def source_list(self) -> list[str]:
        """Channels as ``0049 Channel Name``.

        Numbering is presentation only, but it makes a thousand-entry dropdown
        usable and separates the duplicate names satellite line-ups contain.
        """
        return build_labels(self._state.channels)

    @property
    def media_title(self) -> str | None:
        """The plain channel name, without the number prefix."""
        current = self._state.current
        return current.get("ServiceName") if current else None

    @property
    def media_channel(self) -> str | None:
        current = self._state.current
        if not current:
            return None
        index = current.get("ServiceIndex")
        # The receiver counts from 0 internally but displays channels from 1.
        return str(index + 1) if isinstance(index, int) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        current = self._state.current or {}
        info = self._state.info
        hour, minute = info.get("StbHour"), info.get("StbMin")
        return {
            "service_id": current.get("ServiceID"),
            "channel_index": current.get("ServiceIndex"),
            "scrambled": bool(current.get("Scramble")) or None,
            "channel_count": info.get("ChannelNum"),
            "receiver_time": (
                f"{hour:02d}:{minute:02d}"
                if isinstance(hour, int) and isinstance(minute, int)
                else None
            ),
        }

    async def _send(self, *keys: int) -> None:
        try:
            for index, key in enumerate(keys):
                if index:
                    await asyncio.sleep(KEY_INTERVAL)
                await self.coordinator.client.send_key(key)
        except ViarkError as exc:
            raise HomeAssistantError(f"Viark receiver rejected the key: {exc}") from exc
        await self.coordinator.async_request_refresh()

    async def async_send_key(self, key: str, repeat: int = 1) -> None:
        """Service handler: inject a named or raw key code."""
        from .remote import resolve_key

        await self._send(*([resolve_key(key)] * repeat))

    async def async_media_next_track(self) -> None:
        """Channel up."""
        await self._send(KEY_UP)

    async def async_media_previous_track(self) -> None:
        """Channel down."""
        await self._send(KEY_DOWN)

    async def async_volume_up(self) -> None:
        await self._send(KEY_VOLUME_UP)

    async def async_volume_down(self) -> None:
        await self._send(KEY_VOLUME_DOWN)

    async def async_mute_volume(self, mute: bool) -> None:
        """Toggle mute.

        The receiver exposes only a toggle, so this is a no-op when it already
        matches the requested state.
        """
        if mute == self._state.muted:
            return
        await self._send(KEY_MUTE)

    async def async_turn_off(self) -> None:
        """Put the receiver into standby."""
        if not self._state.powered_on:
            return
        await self._power_toggle()

    async def async_turn_on(self) -> None:
        """Bring the receiver out of soft standby.

        This cannot work from deep standby: the receiver leaves the network
        entirely and nothing can reach it over IP.
        """
        if self._state.powered_on:
            return
        await self._power_toggle()

    async def _power_toggle(self) -> None:
        try:
            await self.coordinator.client.power_toggle()
        except ViarkError as exc:
            raise HomeAssistantError(f"Viark receiver refused the power command: {exc}") from exc
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        """Tune directly to a channel.

        Accepts a label from the dropdown ("0049 Sports HD"), a bare channel
        name, or a bare channel number, so automations written before the source
        list gained numbers keep working unchanged.
        """
        target = resolve(source, self._state.channels)
        if target is None:
            raise ServiceValidationError(f"Unknown Viark channel: {source}")

        program_id = target.get("ServiceID")
        if not program_id:
            raise HomeAssistantError(f"Channel {source} has no usable id")

        try:
            await self.coordinator.client.switch_channel(
                program_id, int(target.get("Radio", 0) or 0)
            )
        except ViarkError as exc:
            # The receiver refuses to retune while a menu is open or the channel
            # is being recorded; both come back as a non-zero status.
            raise HomeAssistantError(f"Could not tune to {source}: {exc}") from exc

        await self.coordinator.async_request_refresh()
