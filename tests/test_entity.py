"""Tests for what every entity shares: one device, named after the receiver."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er


async def test_every_entity_is_named_after_the_receiver(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """No entity may register before the device has a name.

    Before every entity described the device in full, one that set up ahead of
    the media player got an id like remote.none_remote.
    """
    entities = er.async_entries_for_config_entry(
        er.async_get(hass), init_integration.entry_id
    )
    devices = dr.async_entries_for_config_entry(
        dr.async_get(hass), init_integration.entry_id
    )

    assert len(devices) == 1
    assert {entity.device_id for entity in entities} == {devices[0].id}
    ids = {entity.entity_id for entity in entities}
    assert {
        "media_player.viark_sat_4k",
        "remote.viark_sat_4k_remote",
        "binary_sensor.viark_sat_4k_satellite_menu",
        "sensor.viark_sat_4k_serial_number",
    } <= ids
    assert all(entity_id.split(".")[1].startswith("viark_sat_4k") for entity_id in ids)


async def test_unique_ids_are_unchanged(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Changing them would orphan every existing entity and its history."""
    entry_id = init_integration.entry_id
    unique_ids = {
        entity.unique_id
        for entity in er.async_entries_for_config_entry(er.async_get(hass), entry_id)
    }

    assert entry_id in unique_ids  # the media player
    assert f"{entry_id}_remote" in unique_ids
    assert f"{entry_id}_satellite_menu" in unique_ids
    assert f"{entry_id}_serial_number" in unique_ids
