"""Receiver data and a client mock shared by the tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from custom_components.viark.protocol import LOGIN_BLOCK_LENGTH, parse_login_block

HOST = "192.168.1.50"
PORT = 20000
SERIAL = "123456654321"
PRODUCT_NAME = "VIARK SAT 4K"


def make_login(flags: int = 0x44) -> dict[str, Any]:
    """Decode a login block shaped like the one a Viark SAT 4K sends.

    Built and parsed rather than written as a dict, so the fixture cannot drift
    from what parse_login_block really returns.
    """
    plain = bytearray(LOGIN_BLOCK_LENGTH)
    plain[0:12] = b"39WwijOog54a"
    plain[12:15] = (123456).to_bytes(3, "big")
    plain[15:18] = (654321).to_bytes(3, "big")
    plain[20:32] = PRODUCT_NAME.encode()
    plain[52:60] = bytes(range(8))
    plain[60:68] = bytes(range(8, 16))
    plain[68:72] = bytes([50, 1, 168, 192])
    plain[72] = 140
    plain[73:75] = (132).to_bytes(2, "big")
    plain[84] = flags
    return parse_login_block(bytes(b ^ 0x5B for b in reversed(bytes(plain))))


def make_state(**overrides: Any) -> dict[str, Any]:
    """Return the merged state blob (request 14) of a running receiver."""
    state = {
        "ProductName": PRODUCT_NAME,
        "SoftwareVersion": "1.32",
        "SerialNumber": SERIAL,
        "ChannelNum": len(CHANNELS),
        "MaxNumOfPrograms": 20000,
        "PowerMode": 1,
        "StbHour": 16,
        "StbMin": 5,
    }
    state.update(overrides)
    return state


CHANNELS: list[dict[str, Any]] = [
    {"ServiceID": "101", "ServiceName": "News HD", "ServiceIndex": 0, "Radio": 0},
    {
        "ServiceID": "102",
        "ServiceName": "Sports HD",
        "ServiceIndex": 1,
        "Radio": 0,
        "Scramble": 1,
    },
    {"ServiceID": "103", "ServiceName": "Jazz FM", "ServiceIndex": 2, "Radio": 1},
]


def make_client() -> MagicMock:
    """Return a client mock answering like a receiver tuned to Sports HD."""
    client = MagicMock()
    client.info = make_login()
    client.on_notification = None
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.state = AsyncMock(return_value=make_state())
    client.channels = AsyncMock(return_value=CHANNELS)
    client.playing_program_id = AsyncMock(return_value="102")
    client.mute_state = AsyncMock(return_value=False)
    client.send_key = AsyncMock()
    client.switch_channel = AsyncMock()
    client.power_toggle = AsyncMock()
    return client
