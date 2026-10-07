"""Tests for the client's high-level requests.

The wire format and reconnection are covered against a stub receiver in
test_protocol and test_reconnect. These replace request() itself, to pin which
requests each call makes and how it reads the replies.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, call

import pytest

from custom_components.viark.protocol import (
    CHANNEL_PAGE_SIZE,
    REQ_CHANNEL_LIST,
    REQ_MERGED_STATE,
    REQ_MUTE_STATE,
    REQ_PLAYING_CHANNEL,
    REQ_POWER,
    REQ_SATELLITE_LIST,
    REQ_SEND_KEY,
    REQ_STB_INFO,
    REQ_SWITCH_CHANNEL,
    ViarkClient,
    ViarkRequestError,
)


def client_answering(*answers: object) -> ViarkClient:
    """Return a client whose requests get these replies, in order.

    An exception in the list is raised by that request instead.
    """
    client = ViarkClient("192.0.2.1")
    client.request = AsyncMock(side_effect=list(answers))
    return client


async def test_state_reads_the_merged_blob() -> None:
    client = client_answering([{"ProductName": "VIARK SAT 4K"}])

    assert await client.state() == {"ProductName": "VIARK SAT 4K"}
    client.request.assert_awaited_once_with(REQ_MERGED_STATE)


@pytest.mark.parametrize(
    "merged",
    [ViarkRequestError(REQ_MERGED_STATE, 1), [], None],
    ids=["refused", "empty", "no-body"],
)
async def test_state_falls_back_to_the_info_request(merged: object) -> None:
    """Firmware without request 14 still answers the documented request 15."""
    client = client_answering(merged, {"ProductName": "VIARK SAT 4K"})

    assert await client.state() == {"ProductName": "VIARK SAT 4K"}
    assert client.request.await_args_list == [
        call(REQ_MERGED_STATE),
        call(REQ_STB_INFO),
    ]


async def test_channels_are_read_in_pages() -> None:
    """The receiver returns at most CHANNEL_PAGE_SIZE records per request."""
    last = 2 * CHANNEL_PAGE_SIZE + 49
    pages = [
        [
            {"ServiceIndex": i}
            for i in range(start, min(start + CHANNEL_PAGE_SIZE, last + 1))
        ]
        for start in range(0, last + 1, CHANNEL_PAGE_SIZE)
    ]
    client = client_answering(*pages)

    channels = await client.channels(0, last)

    assert [c["ServiceIndex"] for c in channels] == list(range(last + 1))
    assert client.request.await_args_list == [
        call(REQ_CHANNEL_LIST, {"FromIndex": "0", "ToIndex": "99"}),
        call(REQ_CHANNEL_LIST, {"FromIndex": "100", "ToIndex": "199"}),
        call(REQ_CHANNEL_LIST, {"FromIndex": "200", "ToIndex": "249"}),
    ]


async def test_channels_stop_at_an_empty_page() -> None:
    client = client_answering([{"ServiceIndex": 0}], [])

    channels = await client.channels(0, 2 * CHANNEL_PAGE_SIZE)

    assert channels == [{"ServiceIndex": 0}]
    assert client.request.await_count == 2


async def test_channels_without_an_end_ask_how_many_there_are() -> None:
    client = client_answering(
        {"ChannelNum": 2}, [{"ServiceIndex": 0}, {"ServiceIndex": 1}]
    )

    assert len(await client.channels()) == 2
    assert client.request.await_args_list[-1] == call(
        REQ_CHANNEL_LIST, {"FromIndex": "0", "ToIndex": "1"}
    )


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ([{"Data": "00001234567890"}], "00001234567890"),
        ([{"Data": ""}], None),
        ([{}], None),
        (None, None),
    ],
)
async def test_playing_program_id(reply: object, expected: str | None) -> None:
    client = client_answering(reply)

    assert await client.playing_program_id() == expected
    client.request.assert_awaited_once_with(REQ_PLAYING_CHANNEL)


async def test_a_refused_playing_lookup_is_none_unless_strict() -> None:
    """The coordinator needs to tell a refusal from "nothing playing"."""
    refusal = ViarkRequestError(REQ_PLAYING_CHANNEL, 5)

    assert await client_answering(refusal).playing_program_id() is None
    with pytest.raises(ViarkRequestError):
        await client_answering(refusal).playing_program_id(strict=True)


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ([{"Data": "1"}], True),
        ([{"Data": "0"}], False),
        ([{}], None),
        (ViarkRequestError(REQ_MUTE_STATE, 1), None),
    ],
    ids=["muted", "unmuted", "unknown", "refused"],
)
async def test_mute_state(reply: object, expected: bool | None) -> None:
    assert await client_answering(reply).mute_state() is expected


@pytest.mark.parametrize(
    ("reply", "expected"),
    [([{"SatName": "Astra"}], [{"SatName": "Astra"}]), (None, [])],
)
async def test_satellites(reply: object, expected: list) -> None:
    client = client_answering(reply)

    assert await client.satellites() == expected
    client.request.assert_awaited_once_with(REQ_SATELLITE_LIST)


async def test_keys_are_sent_one_request_each_without_waiting() -> None:
    """The receiver never answers a key, so waiting would only time out."""
    client = client_answering(None, None)

    await client.send_key(23, "12")

    assert client.request.await_args_list == [
        call(REQ_SEND_KEY, {"array": [{"KeyValue": "23"}]}, expect_reply=False),
        call(REQ_SEND_KEY, {"array": [{"KeyValue": "12"}]}, expect_reply=False),
    ]


async def test_switch_channel() -> None:
    client = client_answering(None)

    await client.switch_channel("00001234567890", tv_state=1)

    client.request.assert_awaited_once_with(
        REQ_SWITCH_CHANNEL,
        {"array": [{"TvState": "1", "ProgramId": "00001234567890"}]},
    )


async def test_power_toggle_does_not_wait() -> None:
    client = client_answering(None)

    await client.power_toggle()

    client.request.assert_awaited_once_with(REQ_POWER, expect_reply=False)


async def test_the_client_is_a_context_manager() -> None:
    client = ViarkClient("192.0.2.1")
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()

    async with client as entered:
        assert entered is client
        client.connect.assert_awaited_once()
        client.disconnect.assert_not_awaited()

    client.disconnect.assert_awaited_once()
