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
# A code earns an alias one of two ways: the GMScreen Android app and the
# PC-GMScreen Java client independently agree on it, or it was confirmed by
# pressing it on a real receiver and watching the TV.
#
# Still unaliased, documented by a single source and never tested: 25, 27, 28, 40,
# 41, 46-53, 56, 66-68, 71-81 (PC only) and 82 Home (Android only). They can still
# be sent as raw numbers through the send_key service.
#
# Hardware-confirmed, single-source (names taken from the physical remote's own
# labels, which proved more accurate than either document):
#   24 Resol . 26 Timer . 44 F1 . 45 F2 . 54 Audio . 55 freeze . 69/70 CH+/CH-
# Hardware-confirmed and already agreed: 1 and 2 change channel on live TV, 7 exits
# an overlay, 23 toggles mute (checked by reading the mute state back), 63 pauses
# USB media playback.
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

#: The receiver's own CH+/CH- keys. One channel at a time on live TV, ten rows at a
#: time in the EPG or channel list -- exactly what the physical remote does.
KEY_CHANNEL_UP: Final = 69
KEY_CHANNEL_DOWN: Final = 70

#: Freezes the picture and stops the audio; sending it again resumes live TV, and so
#: does KEY_EXIT. No button on the physical remote reaches this, and the receiver
#: reports nothing while frozen, so no entity state is derived from it.
KEY_FREEZE: Final = 55

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
    "audio": 54,
    "freeze": KEY_FREEZE,
    "resolution": 24,
    "timer": 26,
    "f1": 44,
    "f2": 45,
    "info": 57,
    "record": 58,
    "rewind": 59,
    "fast_forward": 60,
    "play": 61,
    "stop": 62,
    "pause": 63,
    "previous": 64,
    "next": 65,
    # The receiver's real CH+/CH- keys. These were aliased to the up/down arrows
    # until 69/70 were confirmed on the hardware; the arrows only step the channel
    # on live TV, whereas these are the keys the remote itself labels CH+/CH-.
    "channel_up": KEY_CHANNEL_UP,
    "channel_down": KEY_CHANNEL_DOWN,
    **{f"digit_{d}": KEY_DIGIT_BASE + d for d in range(10)},
}
