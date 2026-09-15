"""Guard against Home Assistant APIs that are scheduled for removal.

These are source scans rather than imports: the integration modules pull in
``homeassistant.*``, which the rest of the suite deliberately avoids so the tests
run without a Home Assistant install.

A deprecated API keeps working until its removal release, so the cost of missing
one is not a broken build -- it is a warning in every user's log until the day the
integration stops loading. Cheap to pin here instead.
"""

from __future__ import annotations

from pathlib import Path

import pytest

INTEGRATION = Path(__file__).resolve().parents[1] / "custom_components" / "viark"

SOURCES = sorted(INTEGRATION.glob("*.py"))

#: symbol -> the release that removes it, for the error message.
REMOVED_APIS = {
    # Deprecated in favour of MediaPlayerState.OFF / IDLE. The receiver's soft
    # standby maps to OFF; IDLE means powered up with no channel.
    "MediaPlayerState.STANDBY": "2026.8",
}


def test_the_scan_actually_sees_the_integration():
    """A typo in the glob would make every test below pass vacuously."""
    assert SOURCES, f"no Python sources found under {INTEGRATION}"
    assert (INTEGRATION / "media_player.py") in SOURCES


@pytest.mark.parametrize("symbol", sorted(REMOVED_APIS))
def test_removed_api_is_not_used(symbol):
    offenders = [
        f"{path.name}:{number}"
        for path in SOURCES
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if symbol in line and not line.lstrip().startswith("#")
    ]
    assert not offenders, (
        f"{symbol} is removed in Home Assistant {REMOVED_APIS[symbol]}; "
        f"still used at {', '.join(offenders)}"
    )


def test_platforms_use_the_config_entry_entities_callback():
    """Config-entry platforms take AddConfigEntryEntitiesCallback, not the old alias.

    No removal has been announced for AddEntitiesCallback, so this is a
    consistency guard rather than a deadline: copying an older platform's
    boilerplate is the easy way to reintroduce it in just one file.
    """
    platforms = [p for p in SOURCES if "async_add_entities" in p.read_text(encoding="utf-8")]
    assert platforms, "no platform modules found"
    for path in platforms:
        text = path.read_text(encoding="utf-8")
        assert "AddConfigEntryEntitiesCallback" in text, f"{path.name} misses the callback type"
        # Substring check: the new name contains the old one, so match the import.
        assert "import AddEntitiesCallback" not in text, f"{path.name} imports the old alias"
