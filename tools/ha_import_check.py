"""Import every integration module against a real Home Assistant install.

Catches breakage that the standalone protocol tests cannot see: wrong helper
import paths, changed entity APIs, bad service registration signatures.

Needs a virtualenv with Home Assistant installed, which is not part of the repo:

    python -m venv .venv-ha
    .venv-ha/Scripts/pip install homeassistant     # Scripts/ -> bin/ on POSIX
    .venv-ha/Scripts/python tools/ha_import_check.py
"""

from __future__ import annotations

import importlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MODULES = [
    "custom_components.viark.const",
    "custom_components.viark.protocol",
    "custom_components.viark.coordinator",
    "custom_components.viark.config_flow",
    "custom_components.viark",
    "custom_components.viark.media_player",
    "custom_components.viark.remote",
    "custom_components.viark.sensor",
    "custom_components.viark.binary_sensor",
]


def main() -> int:
    import homeassistant.const as ha_const

    print(f"Home Assistant {ha_const.__version__} on Python {sys.version.split()[0]}\n")

    failures = 0
    for name in MODULES:
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - reporting tool
            failures += 1
            print(f"  [FAIL] {name}: {type(exc).__name__}: {exc}")
            traceback.print_exc()
        else:
            print(f"  [ OK ] {name}")

    print()
    if failures:
        print(f"{failures} module(s) failed to import")
        return 1

    # Spot-check the pieces Home Assistant will actually touch.
    from custom_components.viark.binary_sensor import BINARY_SENSORS
    from custom_components.viark.config_flow import ViarkConfigFlow
    from custom_components.viark.media_player import ViarkMediaPlayer
    from custom_components.viark.remote import ViarkRemote, resolve_key
    from custom_components.viark.sensor import SENSORS

    assert ViarkConfigFlow.VERSION == 1
    assert resolve_key("mute") == 23
    assert resolve_key("digit_7") == 19
    assert resolve_key("82") == 82
    print("config flow, entity classes and key resolution all import cleanly")
    print(f"  media_player features: {ViarkMediaPlayer._attr_supported_features}")
    print(f"  remote entity name:    {ViarkRemote._attr_name}")
    print(f"  diagnostic sensors:    {len(SENSORS)} "
          f"({sum(d.entity_registry_enabled_default for d in SENSORS)} enabled by default)")
    print(f"  binary sensors:        {len(BINARY_SENSORS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
