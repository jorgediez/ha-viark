"""The Viark satellite receiver integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import ViarkConfigEntry, ViarkCoordinator
from .protocol import ViarkClient, ViarkConnectionError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.MEDIA_PLAYER,
    Platform.REMOTE,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ViarkConfigEntry) -> bool:
    """Set up Viark from a config entry."""
    # The receiver identifies clients by uuid and limits how many may connect, so
    # reuse a stable per-entry identity instead of a fresh one on every reload.
    client = ViarkClient(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        client_name="Home Assistant",
        client_uuid=f"ha-{entry.entry_id}",
    )

    try:
        await client.connect()
    except ViarkConnectionError as exc:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={
                "host": entry.data[CONF_HOST],
                "error": str(exc),
            },
        ) from exc

    coordinator = ViarkCoordinator(hass, entry, client)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await client.disconnect()
        raise

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ViarkConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.client.disconnect()
    return unloaded
