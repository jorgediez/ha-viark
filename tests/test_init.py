"""Tests for setting up, reloading and unloading the integration."""

from __future__ import annotations

from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.viark.protocol import ViarkConnectionError, ViarkRequestError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .common import HOST, PORT


async def test_setup_and_unload(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    # A stable per-entry identity, so a reload does not take a second client slot.
    mock_client.client_class.assert_called_once_with(
        HOST,
        PORT,
        client_name="Home Assistant",
        client_uuid=f"ha-{config_entry.entry_id}",
    )
    mock_client.connect.assert_awaited_once()
    mock_client.disconnect.assert_not_awaited()

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED
    mock_client.disconnect.assert_awaited_once()


async def test_an_unreachable_receiver_is_retried(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    mock_client.connect.side_effect = ViarkConnectionError("deep standby")
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_a_failed_first_refresh_releases_the_connection(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    """The receiver has few client slots; a retry must not leak one."""
    mock_client.state.side_effect = ViarkRequestError(15, 5)
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    mock_client.disconnect.assert_awaited_once()


async def test_an_empty_state_is_a_failed_refresh(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> None:
    mock_client.state.return_value = {}
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_changing_the_address_reloads(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """The config flow updates the host of a receiver that moved; it must apply."""
    new_host = "192.168.1.77"

    hass.config_entries.async_update_entry(
        init_integration, data={**init_integration.data, CONF_HOST: new_host}
    )
    await hass.async_block_till_done()

    assert init_integration.state is ConfigEntryState.LOADED
    assert mock_client.client_class.call_count == 2
    assert mock_client.client_class.call_args.args[0] == new_host
    mock_client.disconnect.assert_awaited_once()
