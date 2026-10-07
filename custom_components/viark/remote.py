"""Remote entity for the Viark satellite receiver.

Exposes the receiver's key injection (request 1040) as a Home Assistant remote.
``remote.send_command`` takes either a named key from the verified table or a raw
numeric code, so buttons outside that table remain reachable.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
import logging
from typing import Any

from homeassistant.components.remote import RemoteEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, KEY_ALIASES
from .coordinator import ViarkConfigEntry, ViarkCoordinator
from .entity import ViarkEntity
from .protocol import ViarkError

_LOGGER = logging.getLogger(__name__)

DEFAULT_DELAY = 0.45

# Commands share one connection, and the receiver drops keys sent too close
# together.
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ViarkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Viark remote."""
    async_add_entities([ViarkRemote(entry.runtime_data)])


def resolve_key(command: str) -> int:
    """Turn a command into a raw key code.

    Accepts a known alias ("mute", "digit_7") or a raw key code. A bare number
    is always a raw code: "7" sends code 7, not the 7 key, which is "digit_7".
    Codes that only one of the two reference clients documents are not aliased,
    but can still be sent as raw numbers.
    """
    key = command.strip().lower()
    if key in KEY_ALIASES:
        return KEY_ALIASES[key]
    try:
        value = int(key)
    except ValueError:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unknown_key",
            translation_placeholders={
                "key": command,
                "keys": ", ".join(sorted(KEY_ALIASES)),
            },
        ) from None
    if value < 0:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="negative_key",
            translation_placeholders={"key": command},
        )
    return value


class ViarkRemote(ViarkEntity, RemoteEntity):
    """Sends raw remote key codes to the receiver."""

    _attr_translation_key = "remote"

    def __init__(self, coordinator: ViarkCoordinator) -> None:
        """Initialise from the shared coordinator."""
        super().__init__(coordinator, "remote")

    @property
    def is_on(self) -> bool:
        """Return whether the receiver is running rather than in standby."""
        state = self.coordinator.data
        return bool(state and state.powered_on)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Wake the receiver from standby."""
        if self.is_on:
            return
        await self._async_power_toggle()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Put the receiver into standby."""
        if not self.is_on:
            return
        await self._async_power_toggle()

    async def _async_power_toggle(self) -> None:
        try:
            await self.coordinator.client.power_toggle()
        except ViarkError as exc:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="power_refused",
                translation_placeholders={"error": str(exc)},
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
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="key_rejected",
                translation_placeholders={"error": str(exc)},
            ) from exc

        await self.coordinator.async_request_refresh()
