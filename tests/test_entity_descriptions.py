"""Tests for the diagnostic sensor and binary sensor descriptions.

These exercise the value functions and the registry metadata directly; the
entities themselves are covered in test_sensor.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

from custom_components.viark import binary_sensor, sensor

from .common import make_login

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "viark"


STATE = {
    "SerialNumber": "123456654321",
    "SoftwareVersion": "1.32",
    "ChannelNum": 1005,
    "MaxNumOfPrograms": 20000,
    "StbHour": 16,
    "StbMin": 5,
}


def _value(key: str):
    description = next(d for d in sensor.SENSORS if d.key == key)
    return description.value_fn(make_login(), STATE)


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("serial_number", "123456654321"),
        ("software_version", "1.32"),
        ("ip_address", "192.168.1.50"),
        ("platform_id", 140),
        ("channel_count", 1005),
        ("receiver_clock", "16:05"),
        ("data_format", "JSON"),  # flags 0x44 has bit6 set
        ("customer_id", 0),
        ("model_id", 0),
        ("software_version_raw", 132),
        ("max_channels", 20000),
    ],
)
def test_sensor_values(key, expected):
    assert _value(key) == expected


def test_chip_ids_are_hex_strings():
    assert _value("cpu_chip_id") == "0001020304050607"
    assert _value("flash_id") == "08090a0b0c0d0e0f"


def test_receiver_clock_is_none_without_a_clock():
    description = next(d for d in sensor.SENSORS if d.key == "receiver_clock")
    assert description.value_fn(make_login(), {}) is None


def test_sensor_keys_are_unique():
    keys = [d.key for d in sensor.SENSORS]
    assert len(keys) == len(set(keys))


def test_obscure_identifiers_are_disabled_by_default():
    """Noisy identifiers should not clutter a fresh install."""
    disabled = {d.key for d in sensor.SENSORS if not d.entity_registry_enabled_default}
    assert {"cpu_chip_id", "flash_id", "satip_mode", "client_type"} <= disabled

    enabled = {d.key for d in sensor.SENSORS if d.entity_registry_enabled_default}
    assert {"serial_number", "software_version", "channel_count"} <= enabled


def test_every_sensor_is_diagnostic():
    for description in sensor.SENSORS:
        assert description.entity_category == "diagnostic"


def test_binary_sensor_values():
    login = make_login()
    values = {d.key: d.value_fn(login) for d in binary_sensor.BINARY_SENSORS}
    assert values["satellite_menu"] is True


def test_every_entity_has_a_translated_name():
    """A missing translation key shows up as an ugly entity id in the UI."""
    import json

    named = json.loads((ROOT / "translations" / "en.json").read_text(encoding="utf-8"))[
        "entity"
    ]

    for description in sensor.SENSORS:
        assert description.translation_key in named["sensor"], (
            f"{description.key} missing from en.json"
        )
    for description in binary_sensor.BINARY_SENSORS:
        assert description.translation_key in named["binary_sensor"], (
            f"{description.key} missing from en.json"
        )


def test_every_entity_has_an_icon():
    """Without an icon translation the frontend falls back to a generic dot."""
    import json

    icons = json.loads((ROOT / "icons.json").read_text(encoding="utf-8"))["entity"]

    for description in sensor.SENSORS:
        assert description.translation_key in icons["sensor"], (
            f"{description.key} missing from icons.json"
        )
    for description in binary_sensor.BINARY_SENSORS:
        assert description.translation_key in icons["binary_sensor"], (
            f"{description.key} missing from icons.json"
        )


def test_no_orphaned_icons():
    import json

    icons = json.loads((ROOT / "icons.json").read_text(encoding="utf-8"))["entity"]
    assert set(icons["sensor"]) == {d.translation_key for d in sensor.SENSORS}
    assert set(icons["binary_sensor"]) == {
        d.translation_key for d in binary_sensor.BINARY_SENSORS
    }


def test_service_icons_match_declared_services():
    """A service icon keyed to a non-existent service is silently ignored."""
    import json

    import yaml

    icons = json.loads((ROOT / "icons.json").read_text(encoding="utf-8"))
    services = yaml.safe_load((ROOT / "services.yaml").read_text(encoding="utf-8"))
    assert set(icons["services"]) == set(services)


def test_no_orphaned_translations():
    """Names left behind after an entity is removed should not linger."""
    import json

    named = json.loads((ROOT / "translations" / "en.json").read_text(encoding="utf-8"))[
        "entity"
    ]
    assert set(named["sensor"]) == {d.translation_key for d in sensor.SENSORS}
    assert set(named["binary_sensor"]) == {
        d.translation_key for d in binary_sensor.BINARY_SENSORS
    }


def test_receiver_full_flag_is_not_exposed_as_an_entity():
    """It can never be true for a connected client, so it must not be a sensor.

    The client refuses to finish logging in when the flag is set, so an entity
    reading it from the login block would be permanently false and misleading.
    """
    keys = {d.key for d in binary_sensor.BINARY_SENSORS}
    keys |= {d.key for d in sensor.SENSORS}
    assert "client_slots_full" not in keys
    assert "connected_full" not in keys


def test_every_raised_error_has_a_message():
    """A missing message shows the bare translation key to the user."""
    import json

    raised = {
        match
        for path in ROOT.glob("*.py")
        for match in re.findall(
            r'translation_domain=DOMAIN,\s*translation_key="(\w+)"',
            path.read_text(encoding="utf-8"),
        )
    }
    messages = json.loads(
        (ROOT / "translations" / "en.json").read_text(encoding="utf-8")
    )["exceptions"]

    assert raised, "the scan found no translated errors"
    assert raised == set(messages)
