"""Tests for the diagnostic sensor and binary sensor entities.

The value functions are covered in test_entity_descriptions; these check what
Home Assistant ends up with: states, and which entities a fresh install enables.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.viark.const import DOMAIN
from homeassistant.const import STATE_ON, EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .common import SERIAL


def entity_id(hass: HomeAssistant, entry: MockConfigEntry, platform: str, key: str):
    """Return the entity id registered for a description key."""
    return er.async_get(hass).async_get_entity_id(
        platform, DOMAIN, f"{entry.entry_id}_{key}"
    )


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("serial_number", SERIAL),
        ("software_version", "1.32"),
        ("ip_address", "192.168.1.50"),
        ("platform_id", "140"),
        ("channel_count", "3"),
        ("receiver_clock", "16:05"),
    ],
)
async def test_enabled_sensors_report_the_receiver(
    hass: HomeAssistant, init_integration: MockConfigEntry, key: str, expected: str
) -> None:
    state = hass.states.get(entity_id(hass, init_integration, Platform.SENSOR, key))

    assert state is not None
    assert state.state == expected


@pytest.mark.parametrize(
    "key",
    [
        "data_format",
        "cpu_chip_id",
        "flash_id",
        "customer_id",
        "model_id",
        "software_version_raw",
        "software_sub_version",
        "max_channels",
        "satip_mode",
        "client_type",
    ],
)
async def test_obscure_identifiers_start_disabled(
    hass: HomeAssistant, init_integration: MockConfigEntry, key: str
) -> None:
    registry = er.async_get(hass)
    entry = registry.async_get(entity_id(hass, init_integration, Platform.SENSOR, key))

    assert entry is not None
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
    assert entry.entity_category is EntityCategory.DIAGNOSTIC


async def test_satellite_menu(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The fixture's login flags (0x44) have the satellite-menu bit set."""
    state = hass.states.get(
        entity_id(hass, init_integration, Platform.BINARY_SENSOR, "satellite_menu")
    )

    assert state is not None
    assert state.state == STATE_ON
