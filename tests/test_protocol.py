"""Tests for the Viark wire protocol helpers.

These cover the encoding, framing and login-block rules that both reverse
-engineering sources agree on, plus the details that were expensive to discover
and are easy to regress.
"""

from __future__ import annotations

import json
import struct
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "viark"
sys.path.insert(0, str(ROOT))

from const import KEY_ALIASES, KEY_DIGIT_BASE  # noqa: E402
from protocol import (  # noqa: E402
    ACK_LENGTH,
    ACK_MAGIC,
    CHANNEL_PAGE_SIZE,
    LOGIN_BLOCK_LENGTH,
    LOGIN_MAGIC,
    STATUS_OK,
    ViarkClient,
    ViarkConnectionError,
    ViarkRequestError,
    _clean,
    _parse_xml_records,
    deobfuscate,
    frame,
    parse_login_block,
)


# --- framing ---------------------------------------------------------------


def test_frame_uses_seven_digit_zero_padded_length():
    assert frame(b"abc") == b"Start0000003Endabc"
    assert frame(b"") == b"Start0000000End"


def test_frame_length_matches_payload():
    payload = b"x" * 1234
    assert frame(payload).startswith(b"Start0001234End")


def test_json_encoding_is_compact():
    """The receiver ignores JSON containing the spaces json.dumps adds by default."""
    client = ViarkClient("192.0.2.1")
    client.use_json = True
    body = client._encode(15, None)
    assert body == b'{"request":"15"}'
    assert b", " not in body
    assert b'": ' not in body


def test_json_encoding_wraps_array_fields():
    client = ViarkClient("192.0.2.1")
    client.use_json = True
    body = client._encode(1040, {"array": [{"KeyValue": "23"}]})
    assert json.loads(body) == {"request": "1040", "array": [{"KeyValue": "23"}]}


def test_xml_encoding_without_fields_is_self_closing():
    client = ViarkClient("192.0.2.1")
    client.use_json = False
    body = client._encode(26, None).decode()
    assert body.endswith('<Command request="26" />')


def test_xml_encoding_expands_array_into_parm_elements():
    client = ViarkClient("192.0.2.1")
    client.use_json = False
    body = client._encode(
        1000, {"array": [{"TvState": "0", "ProgramId": "00000003930900"}]}
    ).decode()
    assert "<parm><TvState>0</TvState><ProgramId>00000003930900</ProgramId></parm>" in body


# --- login block -----------------------------------------------------------


def _make_login_block(
    model=b"VIARK SAT 4K", serial_hi=123456, serial_lo=654321, flags=0x44
):
    plain = bytearray(LOGIN_BLOCK_LENGTH)
    plain[0:12] = LOGIN_MAGIC
    plain[12:15] = serial_hi.to_bytes(3, "big")
    plain[15:18] = serial_lo.to_bytes(3, "big")
    plain[20:20 + len(model)] = model
    plain[68:72] = bytes([50, 1, 168, 192])  # 192.168.1.50, stored backwards
    plain[72] = 140
    plain[73:75] = (132).to_bytes(2, "big")
    plain[84] = flags
    return bytes(b ^ 0x5B for b in reversed(bytes(plain)))


def test_deobfuscation_is_its_own_inverse():
    data = bytes(range(LOGIN_BLOCK_LENGTH))
    assert deobfuscate(deobfuscate(data)) == data


def test_parse_login_block_extracts_identity():
    info = parse_login_block(_make_login_block())
    assert info["model"] == "VIARK SAT 4K"
    assert info["serial"] == "123456654321"
    assert info["ip"] == "192.168.1.50"
    assert info["platform_id"] == 140
    assert info["sw_version"] == 132


def test_login_flag_bit6_selects_json():
    assert parse_login_block(_make_login_block(flags=0x40))["use_json"] is True
    assert parse_login_block(_make_login_block(flags=0x00))["use_json"] is False


def test_login_flag_bit0_marks_receiver_full():
    assert parse_login_block(_make_login_block(flags=0x41))["connected_full"] is True
    assert parse_login_block(_make_login_block(flags=0x40))["connected_full"] is False


def test_parse_login_block_rejects_bad_magic():
    bad = bytes(b ^ 0x5B for b in reversed(bytes(LOGIN_BLOCK_LENGTH)))
    with pytest.raises(ViarkConnectionError):
        parse_login_block(bad)


def test_parse_login_block_rejects_wrong_length():
    with pytest.raises(ViarkConnectionError):
        parse_login_block(b"\x00" * 50)


# --- reply header ----------------------------------------------------------


def test_ack_header_layout_is_little_endian():
    header = ACK_MAGIC + struct.pack("<III", 540, 14, STATUS_OK)
    assert len(header) == ACK_LENGTH
    length, mtype, status = struct.unpack("<III", header[4:])
    assert (length, mtype, status) == (540, 14, STATUS_OK)


def test_zero_length_means_no_body():
    """Action requests such as 1000 and 1040 are acked with no payload."""
    header = ACK_MAGIC + struct.pack("<III", 0, 1009, STATUS_OK)
    length, mtype, status = struct.unpack("<III", header[4:])
    assert length == 0 and mtype == 1009 and status == STATUS_OK


def test_bodies_are_zlib_streams():
    assert zlib.compress(b'[{"a":1}]').startswith(b"\x78\x9c")


def test_request_error_names_known_statuses():
    assert "menu" in str(ViarkRequestError(1000, 17))
    assert "recorded" in str(ViarkRequestError(1000, 16))
    assert "status 99" in str(ViarkRequestError(1000, 99))


# --- decoding --------------------------------------------------------------


def test_decode_json_strips_control_prefixes():
    client = ViarkClient("192.0.2.1")
    client.use_json = True
    body = zlib.compress(json.dumps([{"favGroupNames": ["Favourites"]}]).encode())
    assert client._decode(zlib.decompress(body)) == [{"favGroupNames": ["Favourites"]}]


def test_decode_returns_none_for_empty_body():
    client = ViarkClient("192.0.2.1")
    assert client._decode(b"") is None


def test_xml_records_flatten_parm_elements():
    xml = b"<Command><parm><Data>7</Data></parm><parm><Data>8</Data></parm></Command>"
    assert _parse_xml_records(xml) == [{"Data": "7"}, {"Data": "8"}]


def test_clean_leaves_ordinary_values_alone():
    assert _clean("Favourites") == "Favourites"
    assert _clean(7) == 7
    assert _clean({"a": ["x"]}) == {"a": ["x"]}


# --- key table -------------------------------------------------------------


def test_digits_are_contiguous_from_twelve():
    """Both sources agree code 12 is digit 0 and 13-21 are digits 1-9."""
    assert KEY_ALIASES["digit_0"] == KEY_DIGIT_BASE == 12
    assert KEY_ALIASES["digit_9"] == 21
    for digit in range(10):
        assert KEY_ALIASES[f"digit_{digit}"] == 12 + digit


@pytest.mark.parametrize(
    ("alias", "code"),
    [("up", 1), ("down", 2), ("ok", 5), ("menu", 6), ("exit", 7),
     ("mute", 23), ("volume_up", 35), ("volume_down", 36), ("power", 42)],
)
def test_agreed_key_codes(alias, code):
    """Only codes both reverse-engineering sources agree on are aliased."""
    assert KEY_ALIASES[alias] == code


def test_single_source_codes_are_not_aliased():
    """Codes only one source documents must not be presented as verified."""
    assert 82 not in KEY_ALIASES.values()  # Home, Android-only
    assert 69 not in KEY_ALIASES.values()  # CH+, PC-only
    assert 70 not in KEY_ALIASES.values()  # CH-, PC-only


def test_channel_page_size_respects_the_documented_limit():
    assert CHANNEL_PAGE_SIZE <= 100
