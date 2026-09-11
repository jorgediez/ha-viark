"""Remote entity for the Viark satellite receiver.

Exposes the receiver's key injection (request 1040) as a Home Assistant remote.
``remote.send_command`` takes either a named key from the verified table or a raw
numeric code, so buttons outside that table remain reachable.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import RemoteEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ViarkConfigEntry
from .const import DOMAIN, KEY_ALIASES
from .coordinator import ViarkCoordinator
from .protocol import ViarkError

_LOGGER = logging.getLogger(__name__)

DEFAULT_DELAY = 0.45


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ViarkConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Viark remote."""
    async_add_entities([ViarkRemote(entry.runtime_data, entry)])


def resolve_key(command: str) -> int:
    """Turn a command into a raw key code.

    Accepts a known alias ("mute", "digit_7"), a bare digit ("7"), or a raw key
    code. Codes that only one of the two reference clients documents are not
    aliased, but can still be sent as raw numbers.
    """
    key = command.strip().lower()
    if key in KEY_ALIASES:
        return KEY_ALIASES[key]
    try:
        value = int(key)
    except ValueError:
        raise ServiceValidationError(
            f"Unknown Viark key {command!r}. Use a raw key code number or one of: "
            f"{', '.join(sorted(KEY_ALIASES))}"
        ) from None
    if value < 0:
        raise ServiceValidationError(f"Key code must not be negative: {command!r}")
    return value


class ViarkRemote(CoordinatorEntity[ViarkCoordinator], RemoteEntity):
    """Sends raw remote key codes to the receiver."""

    _attr_has_entity_name = True
    _attr_name = "Remote"

    def __init__(self, coordinator: ViarkCoordinator, entry: ViarkConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_remote"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def is_on(self) -> bool:
        state = self.coordinator.data
        return bool(state and state.powered_on)

    async def async_turn_on(self, **kwargs: Any) -> None:
        if self.is_on:
            return
        await self._async_power_toggle()

    async def async_turn_off(self, **kwargs: Any) -> None:
        if not self.is_on:
            return
        await self._async_power_toggle()

    async def _async_power_toggle(self) -> None:
        try:
            await self.coordinator.client.power_toggle()
        except ViarkError as exc:
            raise HomeAssistantError(
                f"Viark receiver refused the power command: {exc}"
            ) from exc
        await self.coordinator.async_request_refresh()

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send one or more key codes."""
        delay = kwargs.get("delay_secs") or DEFAULT_DELAY
        repeats = kwargs.get("num_repeats") or 1

        codes = [resolve_key(c) for c in command]
        try:
            first = True
            for _ in range(repeats):
                for code in codes:
                    if not first:
                        await asyncio.sleep(delay)
                    first = False
                    await self.coordinator.client.send_key(code)
        except ViarkError as exc:
            raise HomeAssistantError(f"Viark receiver rejected the key: {exc}") from exc

        await self.coordinator.async_request_refresh()
