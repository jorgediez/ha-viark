"""Channel list presentation helpers.

The receiver can hold a thousand or more channels, so the media player's source
list prefixes each name with its on-screen channel number. That is purely a
display concern -- tuning still goes through the channel's ServiceID -- but it
makes a long dropdown navigable and, importantly, disambiguates the duplicate
channel names that satellite line-ups routinely contain.

Kept free of Home Assistant imports so it can be tested on its own.
"""

from __future__ import annotations

from typing import Any

#: Separates the channel number from the name in a source label.
SEPARATOR = " "


def label_width(channel_count: int) -> int:
    """Digits needed to number `channel_count` channels.

    Numbers are zero padded so labels sort correctly whether the frontend keeps
    the list in receiver order or sorts it as text.
    """
    return max(len(str(max(channel_count, 1))), 1)


def on_screen_number(channel: dict[str, Any]) -> int | None:
    """The number shown on the TV, which counts from 1, not 0."""
    index = channel.get("ServiceIndex")
    return index + 1 if isinstance(index, int) else None


def format_label(channel: dict[str, Any], width: int) -> str:
    """Render one channel as ``0049 Channel Name``."""
    name = channel.get("ServiceName") or ""
    number = on_screen_number(channel)
    if number is None:
        return name
    return f"{number:0{width}d}{SEPARATOR}{name}"


def build_labels(channels: list[dict[str, Any]]) -> list[str]:
    """Render the whole channel list for a source dropdown."""
    width = label_width(len(channels))
    return [format_label(channel, width) for channel in channels]


def resolve(value: str, channels: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Find the channel a user asked for.

    Accepts, in order of preference:

    * a full label as shown in the dropdown, ``"0049 Sports HD"``
    * a bare channel name, ``"News HD"`` -- so automations written before numbering
      was introduced keep working
    * a bare on-screen number, ``"49"``

    Names are tried before numbers so a channel genuinely called "49" still wins
    over channel number 49.
    """
    if not channels:
        return None

    wanted = value.strip()
    if not wanted:
        return None

    width = label_width(len(channels))
    for channel in channels:
        if format_label(channel, width) == wanted:
            return channel

    for channel in channels:
        if channel.get("ServiceName") == wanted:
            return channel

    # A label whose name has since changed, or a plain number.
    head = wanted.split(SEPARATOR, 1)[0]
    if head.isdigit():
        number = int(head)
        for channel in channels:
            if on_screen_number(channel) == number:
                return channel

    return None
