"""Tests for the diagnostics download."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.viark.diagnostics import async_get_config_entry_diagnostics
from custom_components.viark.protocol import ViarkConnectionError
from homeassistant.core import HomeAssistant

from .common import CHANNELS, HOST, SERIAL, make_state


async def test_diagnostics_describe_the_receiver(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["entry"] == {"host": "**REDACTED**", "port": 20000}
    assert diagnostics["login"]["model"] == "VIARK SAT 4K"
    assert diagnostics["login"]["platform_id"] == 140
    assert diagnostics["connection"] == {"connected": True, "data_format": "JSON"}
    assert diagnostics["coordinator"] == {
        "last_update_success": True,
        "last_exception": None,
    }
    state = diagnostics["state"]
    assert state["values"]["ProductName"] == "VIARK SAT 4K"
    assert state["values"]["PowerMode"] == 1
    assert "StbHour" in state["fields"]
    assert state["channel_count"] == len(CHANNELS)
    assert state["current_channel"] == {"ServiceIndex": 1, "Radio": 0, "Scramble": 1}


async def test_diagnostics_leave_out_what_identifies_a_user(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Address, serial, chip ids and channel names must stay at home."""
    mock_client.state.return_value = make_state(LockPassword="1234")
    await init_integration.runtime_data.async_refresh()

    text = json.dumps(await async_get_config_entry_diagnostics(hass, init_integration))

    for secret in (HOST, SERIAL, "0001020304050607", "08090a0b0c0d0e0f", "1234"):
        assert secret not in text
    for channel in CHANNELS:
        assert channel["ServiceName"] not in text
    # Fields the integration does not know are listed by name only.
    assert "LockPassword" in text


async def test_diagnostics_after_a_failed_refresh(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    mock_client.state.side_effect = ViarkConnectionError("gone")
    await init_integration.runtime_data.async_refresh()

    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["coordinator"]["last_update_success"] is False
    assert "gone" in diagnostics["coordinator"]["last_exception"]
