"""Constants for the Viark satellite receiver integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "viark"

DEFAULT_PORT: Final = 20000
DEFAULT_NAME: Final = "Viark receiver"

#: The receiver pushes notifications when its state changes, so polling is only a
#: backstop against a missed push.
SCAN_INTERVAL_SECONDS: Final = 120

#: Re-reading 1000+ channels is expensive; refresh only when the box says the list
#: changed (notification 2002) or the cache ages out.
CHANNEL_CACHE_REFRESH_SECONDS: Final = 3600

SERVICE_SEND_KEY: Final = "send_key"
ATTR_KEY: Final = "key"
ATTR_REPEAT: Final = "repeat"

# ---------------------------------------------------------------------------
# Remote key codes for request 1040.
#
# This table contains ONLY codes where the GMScreen Android app and the
# PC-GMScreen Java client independently agree. Codes appearing in just one of the
# two sources (24-28, 40, 41, 44-56, 66-82) are deliberately omitted -- they can
# still be sent as raw numbers through the send_key service.
#
# Verified on the hardware: 1 and 2 change channel on live TV, 7 exits an overlay,
# and 23 toggles mute (confirmed by reading the mute state back).
# ---------------------------------------------------------------------------
KEY_UP: Final = 1
KEY_DOWN: Final = 2
KEY_LEFT: Final = 3
KEY_RIGHT: Final = 4
KEY_OK: Final = 5
KEY_MENU: Final = 6
KEY_EXIT: Final = 7
KEY_MUTE: Final = 23
KEY_VOLUME_UP: Final = 35
KEY_VOLUME_DOWN: Final = 36
KEY_PAGE_UP: Final = 37
KEY_PAGE_DOWN: Final = 38
KEY_POWER: Final = 42

#: Digits are contiguous from 0: code 12 is "0", 13 is "1" ... 21 is "9".
KEY_DIGIT_BASE: Final = 12

KEY_ALIASES: Final[dict[str, int]] = {
    "up": KEY_UP,
    "down": KEY_DOWN,
    "left": KEY_LEFT,
    "right": KEY_RIGHT,
    "ok": KEY_OK,
    "select": KEY_OK,
    "menu": KEY_MENU,
    "exit": KEY_EXIT,
    "back": KEY_EXIT,
    "red": 8,
    "green": 9,
    "yellow": 10,
    "blue": 11,
    "tv_radio": 22,
    "mute": KEY_MUTE,
    "recall": 29,
    "satellite": 30,
    "subtitle": 31,
    "epg": 32,
    "favourite": 33,
    "favorite": 33,
    "teletext": 34,
    "volume_up": KEY_VOLUME_UP,
    "volume_down": KEY_VOLUME_DOWN,
    "page_up": KEY_PAGE_UP,
    "page_down": KEY_PAGE_DOWN,
    "find": 39,
    "power": KEY_POWER,
    "usb": 43,
    "info": 57,
    "record": 58,
    "rewind": 59,
    "fast_forward": 60,
    "play": 61,
    "stop": 62,
    "pause": 63,
    "previous": 64,
    "next": 65,
    # Channel stepping: on live TV the up/down arrows move the channel. Verified.
    "channel_up": KEY_UP,
    "channel_down": KEY_DOWN,
    **{f"digit_{d}": KEY_DIGIT_BASE + d for d in range(10)},
}
