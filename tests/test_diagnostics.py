"""Tests for the diagnostic sensor and binary sensor descriptions.

These import the platform modules without Home Assistant, so they exercise the
value functions and the registry metadata rather than the entity plumbing.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "viark"
sys.path.insert(0, str(ROOT))

from protocol import parse_login_block  # noqa: E402


def _stub_homeassistant() -> None:
    """Provide the minimum Home Assistant surface the platforms import.

    Only the descriptor classes and enums are needed to build and evaluate the
    entity descriptions, so stubbing avoids depending on a full HA install.
    """
    if "homeassistant" in sys.modules:
        return

    def module(name: str, **attrs) -> ModuleType:
        mod = ModuleType(name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        sys.modules[name] = mod
        return mod

    # Home Assistant's EntityDescription is a frozen, keyword-only dataclass;
    # the stub must be one too or subclasses lose the inherited fields.
    @dataclass(frozen=True, kw_only=True)
    class _Description:
        key: str
        translation_key: str | None = None
        entity_category: str | None = None
        entity_registry_enabled_default: bool = True
        native_unit_of_measurement: str | None = None
        state_class: str | None = None
        device_class: str | None = None

    module("homeassistant")
    module("homeassistant.const", EntityCategory=SimpleNamespace(DIAGNOSTIC="diagnostic"))
    module("homeassistant.core", HomeAssistant=object, callback=lambda f: f)
    module("homeassistant.components")
    module(
        "homeassistant.components.sensor",
        SensorEntity=object,
        SensorEntityDescription=_Description,
        SensorStateClass=SimpleNamespace(MEASUREMENT="measurement"),
    )
    module(
        "homeassistant.components.binary_sensor",
        BinarySensorEntity=object,
        BinarySensorEntityDescription=_Description,
        BinarySensorDeviceClass=SimpleNamespace(PROBLEM="problem"),
    )
    module("homeassistant.helpers")
    module("homeassistant.helpers.debounce", Debouncer=object)
    module("homeassistant.helpers.device_registry", DeviceInfo=dict)
    module("homeassistant.helpers.event", async_call_later=lambda *a: None)
    module(
        "homeassistant.helpers.entity_platform",
        AddConfigEntryEntitiesCallback=object,
    )

    class _CoordinatorEntity:
        def __class_getitem__(cls, _item):
            return cls

        def __init__(self, *_a, **_kw):
            pass

    module(
        "homeassistant.helpers.update_coordinator",
        CoordinatorEntity=_CoordinatorEntity,
        DataUpdateCoordinator=_CoordinatorEntity,
        UpdateFailed=Exception,
    )


_stub_homeassistant()

# The platform modules import "from . import ViarkConfigEntry"; provide a package
# shim so they can be imported standalone.
_pkg = ModuleType("viark_pkg")
_pkg.__path__ = [str(ROOT)]
_pkg.ViarkConfigEntry = object
sys.modules["viark_pkg"] = _pkg

import importlib.util  # noqa: E402


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"viark_pkg.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sensor = _load("sensor")
binary_sensor = _load("binary_sensor")


def _login() -> dict:
    plain = bytearray(108)
    plain[0:12] = b"39WwijOog54a"
    plain[12:15] = (123456).to_bytes(3, "big")
    plain[15:18] = (654321).to_bytes(3, "big")
    plain[20:32] = b"VIARK SAT 4K"
    plain[52:60] = bytes(range(8))
    plain[60:68] = bytes(range(8, 16))
    plain[68:72] = bytes([50, 1, 168, 192])
    plain[72] = 140
    plain[73:75] = (132).to_bytes(2, "big")
    plain[84] = 0x44
    return parse_login_block(bytes(b ^ 0x5B for b in reversed(bytes(plain))))


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
    return description.value_fn(_login(), STATE)


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
    assert description.value_fn(_login(), {}) is None


def test_sensor_keys_are_unique():
    keys = [d.key for d in sensor.SENSORS]
    assert len(keys) == len(set(keys))


def test_obscure_identifiers_are_disabled_by_default():
    """Noisy identifiers should not clutter a fresh install."""
    disabled = {
        d.key for d in sensor.SENSORS if not d.entity_registry_enabled_default
    }
    assert {"cpu_chip_id", "flash_id", "satip_mode", "client_type"} <= disabled

    enabled = {d.key for d in sensor.SENSORS if d.entity_registry_enabled_default}
    assert {"serial_number", "software_version", "channel_count"} <= enabled


def test_every_sensor_is_diagnostic():
    for description in sensor.SENSORS:
        assert description.entity_category == "diagnostic"


def test_binary_sensor_values():
    login = _login()
    values = {d.key: d.value_fn(login) for d in binary_sensor.BINARY_SENSORS}
    assert values["satellite_menu"] is True


def test_every_entity_has_a_translated_name():
    """A missing translation key shows up as an ugly entity id in the UI."""
    import json

    strings = json.loads((ROOT / "strings.json").read_text(encoding="utf-8"))
    english = json.loads(
        (ROOT / "translations" / "en.json").read_text(encoding="utf-8")
    )

    for source, label in ((strings, "strings.json"), (english, "en.json")):
        named = source["entity"]
        for description in sensor.SENSORS:
            assert description.translation_key in named["sensor"], (
                f"{description.key} missing from {label}"
            )
        for description in binary_sensor.BINARY_SENSORS:
            assert description.translation_key in named["binary_sensor"], (
                f"{description.key} missing from {label}"
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

    named = json.loads((ROOT / "strings.json").read_text(encoding="utf-8"))["entity"]
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
