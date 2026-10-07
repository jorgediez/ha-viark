"""Tests for the remote entity."""

from __future__ import annotations

from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.viark import remote
from custom_components.viark.const import DOMAIN, KEY_DIGIT_BASE, KEY_MUTE
from custom_components.viark.protocol import ViarkConnectionError
from homeassistant.components.remote import (
    ATTR_COMMAND,
    ATTR_DELAY_SECS,
    ATTR_NUM_REPEATS,
    DOMAIN as REMOTE_DOMAIN,
    SERVICE_SEND_COMMAND,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import entity_registry as er

from .common import make_state


@pytest.fixture
def sleeps() -> Generator[AsyncMock]:
    """Record the pauses between keys instead of waiting them out."""
    sleep = AsyncMock()
    with patch.object(remote, "asyncio", SimpleNamespace(sleep=sleep)):
        yield sleep


@pytest.fixture
def entity_id(hass: HomeAssistant, init_integration: MockConfigEntry) -> str:
    """Return the remote's entity id."""
    entity_id = er.async_get(hass).async_get_entity_id(
        REMOTE_DOMAIN, DOMAIN, f"{init_integration.entry_id}_remote"
    )
    assert entity_id
    return entity_id


async def send_command(hass: HomeAssistant, entity_id: str, **data: object) -> None:
    """Call remote.send_command and wait for it to finish."""
    await hass.services.async_call(
        REMOTE_DOMAIN,
        SERVICE_SEND_COMMAND,
        {ATTR_ENTITY_ID: entity_id, **data},
        blocking=True,
    )


async def test_the_remote_follows_power(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    assert hass.states.get(entity_id).state == STATE_ON

    mock_client.state.return_value = make_state(PowerMode=0)
    await init_integration.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_OFF


async def test_send_command_resolves_names_and_raw_codes(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str, sleeps: AsyncMock
) -> None:
    await send_command(
        hass,
        entity_id,
        **{
            ATTR_COMMAND: ["mute", "digit_7", "77"],
            ATTR_NUM_REPEATS: 2,
            ATTR_DELAY_SECS: 1,
        },
    )

    # A bare number is a raw code, not a digit key: digits go by name.
    codes = [KEY_MUTE, KEY_DIGIT_BASE + 7, 77]
    assert mock_client.send_key.await_args_list == [call(code) for code in codes] * 2
    # A pause between every pair of keys, none before the first.
    assert sleeps.await_args_list == [call(1)] * 5


@pytest.mark.parametrize(
    ("command", "error"),
    [("warp_speed", "unknown_key"), ("-1", "negative_key")],
)
async def test_send_command_rejects_bad_keys_before_sending(
    hass: HomeAssistant,
    mock_client: MagicMock,
    entity_id: str,
    command: str,
    error: str,
) -> None:
    with pytest.raises(ServiceValidationError) as raised:
        await send_command(hass, entity_id, **{ATTR_COMMAND: ["mute", command]})
    assert raised.value.translation_key == error
    mock_client.send_key.assert_not_awaited()


async def test_a_rejected_key_is_reported(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    mock_client.send_key.side_effect = ViarkConnectionError("gone")

    with pytest.raises(HomeAssistantError):
        await send_command(hass, entity_id, **{ATTR_COMMAND: ["mute"]})


async def test_power_is_toggled_only_when_needed(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    """The receiver only has a power toggle, so turning on twice must not turn off."""
    service = {ATTR_ENTITY_ID: entity_id}
    await hass.services.async_call(REMOTE_DOMAIN, SERVICE_TURN_ON, service, True)
    mock_client.power_toggle.assert_not_awaited()

    await hass.services.async_call(REMOTE_DOMAIN, SERVICE_TURN_OFF, service, True)
    mock_client.power_toggle.assert_awaited_once()

    mock_client.state.return_value = make_state(PowerMode=0)
    await init_integration.runtime_data.async_refresh()
    await hass.async_block_till_done()
    await hass.services.async_call(REMOTE_DOMAIN, SERVICE_TURN_OFF, service, True)
    await hass.services.async_call(REMOTE_DOMAIN, SERVICE_TURN_ON, service, True)
    assert mock_client.power_toggle.await_count == 2


async def test_a_refused_power_command_is_reported(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    mock_client.power_toggle.side_effect = ViarkConnectionError("gone")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            REMOTE_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, True
        )
