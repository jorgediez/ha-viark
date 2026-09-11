"""Tests for source-list labelling and channel resolution.

The source list is what a user picks from in Home Assistant, and select_source
receives the label back as a plain string, so labelling and resolution have to
stay in step. These also pin the backwards-compatibility promise: automations
written against bare channel names must keep working now that labels carry a
number.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "viark"
sys.path.insert(0, str(ROOT))

from channels import (  # noqa: E402
    build_labels,
    format_label,
    label_width,
    on_screen_number,
    resolve,
)


def channel(index: int, name: str, service_id: str | None = None) -> dict:
    return {
        "ServiceIndex": index,
        "ServiceName": name,
        "ServiceID": service_id or f"{index:014d}",
        "Radio": 0,
    }


SMALL = [channel(0, "News HD"), channel(1, "News 2"), channel(2, "Movies HD")]


def big(count: int = 1005) -> list[dict]:
    return [channel(i, f"Channel {i + 1}") for i in range(count)]


# --- numbering -------------------------------------------------------------


def test_on_screen_number_counts_from_one():
    assert on_screen_number(channel(0, "News HD")) == 1
    assert on_screen_number(channel(48, "Sports HD")) == 49


def test_on_screen_number_is_none_without_an_index():
    assert on_screen_number({"ServiceName": "Orphan"}) is None


@pytest.mark.parametrize(
    ("count", "width"),
    [(1, 1), (9, 1), (10, 2), (99, 2), (100, 3), (1005, 4), (0, 1)],
)
def test_label_width_matches_the_largest_number(count, width):
    assert label_width(count) == width


def test_labels_are_zero_padded_so_they_sort_correctly():
    """The frontend may sort the dropdown as text, so 9 must precede 10."""
    labels = build_labels(big(1005))
    assert labels[0] == "0001 Channel 1"
    assert labels[48] == "0049 Channel 49"
    assert labels[-1] == "1005 Channel 1005"
    assert sorted(labels) == labels


def test_small_lists_are_not_over_padded():
    assert build_labels(SMALL) == ["1 News HD", "2 News 2", "3 Movies HD"]


def test_label_without_an_index_falls_back_to_the_name():
    assert format_label({"ServiceName": "Orphan"}, 4) == "Orphan"


def test_label_of_an_unlabellable_stub_is_empty():
    """A channel playing but absent from the cached list has only a ServiceID.

    The media player turns this empty string into "no source", so it must not
    silently become a label that matches nothing.
    """
    assert format_label({"ServiceID": "00001234567890"}, 4) == ""


def test_labels_are_unique_even_when_names_repeat():
    """Duplicate names are common in satellite line-ups and broke selection."""
    duplicates = [channel(0, "Sport HD"), channel(1, "Sport HD")]
    labels = build_labels(duplicates)
    assert labels == ["1 Sport HD", "2 Sport HD"]
    assert len(set(labels)) == 2


# --- resolution ------------------------------------------------------------


def test_resolve_accepts_a_full_label():
    channels = big(1005)
    assert resolve("0049 Channel 49", channels)["ServiceIndex"] == 48


def test_resolve_accepts_a_bare_name_for_backwards_compatibility():
    """Automations predating numbered labels must keep working."""
    assert resolve("Movies HD", SMALL)["ServiceIndex"] == 2


def test_resolve_accepts_a_bare_number():
    assert resolve("49", big(1005))["ServiceIndex"] == 48
    assert resolve("0049", big(1005))["ServiceIndex"] == 48


def test_resolve_prefers_a_real_name_over_a_channel_number():
    """A channel actually called "2" should win over channel number 2."""
    channels = [channel(0, "2"), channel(1, "News 2")]
    assert resolve("2", channels)["ServiceIndex"] == 0


def test_resolve_prefers_an_exact_label_over_everything():
    channels = [channel(0, "2 News 2"), channel(1, "News 2")]
    assert resolve("2 News 2", channels)["ServiceIndex"] == 1


def test_resolve_tolerates_surrounding_whitespace():
    assert resolve("  News HD  ", SMALL)["ServiceIndex"] == 0


def test_resolve_handles_a_renamed_channel_by_number():
    """A stale label still resolves through its number prefix."""
    assert resolve("0049 Old Name", big(1005))["ServiceIndex"] == 48


def test_resolve_returns_none_for_unknown_input():
    assert resolve("Nope", SMALL) is None
    assert resolve("9999", SMALL) is None
    assert resolve("", SMALL) is None
    assert resolve("News HD", []) is None


def test_every_label_resolves_back_to_its_own_channel():
    """The round trip the media player depends on."""
    channels = big(300)
    for expected, label in zip(channels, build_labels(channels), strict=True):
        assert resolve(label, channels)["ServiceID"] == expected["ServiceID"]
