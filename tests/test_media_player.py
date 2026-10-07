"""Tests for the media player entity and the send_key action."""

from __future__ import annotations

from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.viark import media_player
from custom_components.viark.const import (
    DOMAIN,
    KEY_CHANNEL_DOWN,
    KEY_CHANNEL_UP,
    KEY_MUTE,
    KEY_VOLUME_DOWN,
    KEY_VOLUME_UP,
    SERVICE_SEND_KEY,
)
from custom_components.viark.protocol import (
    NOTIFY_PLAYING_CHANGED,
    ViarkConnectionError,
    ViarkRequestError,
)
from homeassistant.components.media_player import (
    ATTR_INPUT_SOURCE,
    ATTR_INPUT_SOURCE_LIST,
    ATTR_MEDIA_CHANNEL,
    ATTR_MEDIA_TITLE,
    ATTR_MEDIA_VOLUME_MUTED,
    DOMAIN as MP_DOMAIN,
    SERVICE_SELECT_SOURCE,
    MediaPlayerState,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_MEDIA_NEXT_TRACK,
    SERVICE_MEDIA_PREVIOUS_TRACK,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    SERVICE_VOLUME_DOWN,
    SERVICE_VOLUME_MUTE,
    SERVICE_VOLUME_UP,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .common import PRODUCT_NAME, SERIAL, make_state


@pytest.fixture
def sleeps() -> Generator[AsyncMock]:
    """Record the pauses between keys instead of waiting them out."""
    sleep = AsyncMock()
    with patch.object(media_player, "asyncio", SimpleNamespace(sleep=sleep)):
        yield sleep


@pytest.fixture
def entity_id(hass: HomeAssistant, init_integration: MockConfigEntry) -> str:
    """Return the media player's entity id."""
    entity_id = er.async_get(hass).async_get_entity_id(
        MP_DOMAIN, DOMAIN, init_integration.entry_id
    )
    assert entity_id
    return entity_id


async def call_service(
    hass: HomeAssistant, service: str, entity_id: str, **data: object
) -> None:
    """Call a media player action and wait for it to finish."""
    await hass.services.async_call(
        MP_DOMAIN, service, {ATTR_ENTITY_ID: entity_id, **data}, blocking=True
    )


async def refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Refresh the coordinator as a push from the receiver would."""
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


async def test_the_tuned_channel_is_shown(hass: HomeAssistant, entity_id: str) -> None:
    state = hass.states.get(entity_id)

    assert state.state == MediaPlayerState.PLAYING
    assert state.attributes[ATTR_INPUT_SOURCE] == "2 Sports HD"
    assert state.attributes[ATTR_INPUT_SOURCE_LIST] == [
        "1 News HD",
        "2 Sports HD",
        "3 Jazz FM",
    ]
    assert state.attributes[ATTR_MEDIA_TITLE] == "Sports HD"
    assert state.attributes[ATTR_MEDIA_CHANNEL] == "2"
    assert state.attributes[ATTR_MEDIA_VOLUME_MUTED] is False
    assert state.attributes["service_id"] == "102"
    assert state.attributes["channel_index"] == 1
    assert state.attributes["scrambled"] is True
    assert state.attributes["channel_count"] == 3
    assert state.attributes["receiver_time"] == "16:05"


async def test_the_receiver_is_described_as_a_device(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    devices = dr.async_entries_for_config_entry(
        dr.async_get(hass), init_integration.entry_id
    )

    assert len(devices) == 1
    device = devices[0]
    assert device.identifiers == {(DOMAIN, init_integration.entry_id)}
    assert device.manufacturer == "Viark"
    assert device.name == PRODUCT_NAME
    assert device.model == PRODUCT_NAME
    assert device.serial_number == SERIAL
    assert device.sw_version == "1.32"


async def test_standby_is_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    mock_client.state.return_value = make_state(PowerMode=0)
    await refresh(hass, init_integration)

    assert hass.states.get(entity_id).state == MediaPlayerState.OFF


async def test_no_channel_is_idle(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    mock_client.playing_program_id.return_value = None
    await refresh(hass, init_integration)

    state = hass.states.get(entity_id)
    assert state.state == MediaPlayerState.IDLE
    assert ATTR_INPUT_SOURCE not in state.attributes


async def test_a_channel_outside_the_list_has_no_source(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    """A radio channel while the TV list is cached arrives as a bare ServiceID."""
    mock_client.playing_program_id.return_value = "999"
    await refresh(hass, init_integration)

    state = hass.states.get(entity_id)
    assert state.state == MediaPlayerState.PLAYING
    assert ATTR_INPUT_SOURCE not in state.attributes
    assert state.attributes["service_id"] == "999"


async def test_a_lost_receiver_is_unavailable(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    mock_client.state.side_effect = ViarkConnectionError("gone")
    await refresh(hass, init_integration)

    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


async def test_a_push_updates_the_channel(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    mock_client.playing_program_id.return_value = "103"

    mock_client.on_notification(NOTIFY_PLAYING_CHANGED)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).attributes[ATTR_INPUT_SOURCE] == "3 Jazz FM"


@pytest.mark.usefixtures("sleeps")
@pytest.mark.parametrize(
    ("service", "key"),
    [
        (SERVICE_MEDIA_NEXT_TRACK, KEY_CHANNEL_UP),
        (SERVICE_MEDIA_PREVIOUS_TRACK, KEY_CHANNEL_DOWN),
        (SERVICE_VOLUME_UP, KEY_VOLUME_UP),
        (SERVICE_VOLUME_DOWN, KEY_VOLUME_DOWN),
    ],
)
async def test_buttons_send_their_key(
    hass: HomeAssistant,
    mock_client: MagicMock,
    entity_id: str,
    service: str,
    key: int,
) -> None:
    await call_service(hass, service, entity_id)

    mock_client.send_key.assert_awaited_once_with(key)


@pytest.mark.usefixtures("sleeps")
async def test_mute_toggles_only_when_it_changes_something(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    """The receiver only has a mute toggle, so muting twice must not unmute."""
    await call_service(
        hass, SERVICE_VOLUME_MUTE, entity_id, **{ATTR_MEDIA_VOLUME_MUTED: False}
    )
    mock_client.send_key.assert_not_awaited()

    await call_service(
        hass, SERVICE_VOLUME_MUTE, entity_id, **{ATTR_MEDIA_VOLUME_MUTED: True}
    )
    mock_client.send_key.assert_awaited_once_with(KEY_MUTE)


async def test_turning_off_toggles_power_once(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    await call_service(hass, SERVICE_TURN_ON, entity_id)
    mock_client.power_toggle.assert_not_awaited()

    await call_service(hass, SERVICE_TURN_OFF, entity_id)
    mock_client.power_toggle.assert_awaited_once()

    mock_client.state.return_value = make_state(PowerMode=0)
    await refresh(hass, init_integration)
    await call_service(hass, SERVICE_TURN_OFF, entity_id)
    await call_service(hass, SERVICE_TURN_ON, entity_id)
    assert mock_client.power_toggle.await_count == 2


async def test_a_refused_power_command_is_reported(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    mock_client.power_toggle.side_effect = ViarkConnectionError("gone")

    with pytest.raises(HomeAssistantError):
        await call_service(hass, SERVICE_TURN_OFF, entity_id)


@pytest.mark.parametrize(
    ("source", "service_id", "radio"),
    [
        ("3 Jazz FM", "103", 1),  # the label from the dropdown
        ("News HD", "101", 0),  # a bare name, as older automations use
        ("2", "102", 0),  # a bare channel number
    ],
)
async def test_select_source_tunes_directly(
    hass: HomeAssistant,
    mock_client: MagicMock,
    entity_id: str,
    source: str,
    service_id: str,
    radio: int,
) -> None:
    await call_service(
        hass, SERVICE_SELECT_SOURCE, entity_id, **{ATTR_INPUT_SOURCE: source}
    )

    mock_client.switch_channel.assert_awaited_once_with(service_id, radio)


async def test_an_unknown_source_is_rejected(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    with pytest.raises(ServiceValidationError):
        await call_service(
            hass, SERVICE_SELECT_SOURCE, entity_id, **{ATTR_INPUT_SOURCE: "Nope TV"}
        )
    mock_client.switch_channel.assert_not_awaited()


async def test_a_channel_without_an_id_cannot_be_tuned(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
    entity_id: str,
) -> None:
    mock_client.channels.return_value = [
        {"ServiceName": "Broken", "ServiceIndex": 0, "Radio": 0}
    ]
    mock_client.state.return_value = make_state(ChannelNum=1)
    await refresh(hass, init_integration)

    with pytest.raises(HomeAssistantError):
        await call_service(
            hass, SERVICE_SELECT_SOURCE, entity_id, **{ATTR_INPUT_SOURCE: "Broken"}
        )


async def test_a_refused_tune_is_reported(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    """The receiver refuses to retune while a menu is open or it is recording."""
    mock_client.switch_channel.side_effect = ViarkRequestError(1000, 5)

    with pytest.raises(HomeAssistantError):
        await call_service(
            hass, SERVICE_SELECT_SOURCE, entity_id, **{ATTR_INPUT_SOURCE: "News HD"}
        )


async def test_send_key_repeats_with_a_pause(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str, sleeps: AsyncMock
) -> None:
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SEND_KEY,
        {ATTR_ENTITY_ID: entity_id, "key": "mute", "repeat": 3},
        blocking=True,
    )

    assert mock_client.send_key.await_args_list == [call(KEY_MUTE)] * 3
    # The receiver drops keys sent back to back.
    assert sleeps.await_args_list == [call(media_player.KEY_INTERVAL)] * 2


@pytest.mark.usefixtures("sleeps")
async def test_send_key_accepts_a_raw_code(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SEND_KEY,
        {ATTR_ENTITY_ID: entity_id, "key": "77"},
        blocking=True,
    )

    mock_client.send_key.assert_awaited_once_with(77)


async def test_send_key_rejects_an_unknown_name(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SEND_KEY,
            {ATTR_ENTITY_ID: entity_id, "key": "warp_speed"},
            blocking=True,
        )
    mock_client.send_key.assert_not_awaited()


async def test_a_rejected_key_is_reported(
    hass: HomeAssistant, mock_client: MagicMock, entity_id: str
) -> None:
    mock_client.send_key.side_effect = ViarkConnectionError("gone")

    with pytest.raises(HomeAssistantError):
        await call_service(hass, SERVICE_VOLUME_UP, entity_id)
