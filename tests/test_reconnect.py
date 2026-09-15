"""Reconnection behaviour against a stub receiver.

Runs a minimal fake receiver in-process so the failure paths can be exercised
without the real hardware: a dropped connection must be noticed, reported to any
waiter, and healed on the next request.
"""

from __future__ import annotations

import asyncio
import contextlib
import gc
import json
import logging
import struct
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "viark"
sys.path.insert(0, str(ROOT))

from protocol import (  # noqa: E402
    LOGIN_BLOCK_LENGTH,
    LOGIN_MAGIC,
    ViarkClient,
    ViarkConnectionError,
    ViarkError,
    ViarkRequestError,
)


def make_login_block(use_json: bool = True) -> bytes:
    plain = bytearray(LOGIN_BLOCK_LENGTH)
    plain[0:12] = LOGIN_MAGIC
    plain[12:15] = (123456).to_bytes(3, "big")
    plain[15:18] = (654321).to_bytes(3, "big")
    plain[20:32] = b"VIARK SAT 4K"
    plain[68:72] = bytes([50, 1, 168, 192])
    plain[72] = 140
    plain[84] = 0x40 if use_json else 0x00
    return bytes(b ^ 0x5B for b in reversed(bytes(plain)))


def reply(mtype: int, payload=None, status: int = 0) -> bytes:
    if payload is None:
        body = b""
    else:
        body = zlib.compress(json.dumps(payload).encode())
    return b"GCDH" + struct.pack("<III", len(body), mtype, status) + body


class StubReceiver:
    """A fake receiver that speaks just enough of the protocol."""

    def __init__(self) -> None:
        self.server: asyncio.AbstractServer | None = None
        self.port = 0
        self.connections = 0
        self.drop_next = False
        self.status_for: dict[int, int] = {}
        self.writers: list[asyncio.StreamWriter] = []

    async def start(self) -> None:
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self.server.sockets[0].getsockname()[1]

    async def stop(self) -> None:
        # Close client transports first: since Python 3.12 wait_closed() blocks
        # until every connection handler has finished.
        for writer in self.writers:
            with contextlib.suppress(Exception):
                writer.close()
        self.writers.clear()
        if self.server:
            self.server.close()
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self.server.wait_closed(), timeout=5)

    async def _read_frame(self, reader: asyncio.StreamReader) -> dict:
        header = await reader.readexactly(len(b"Start0000000End"))
        length = int(header[5:12])
        body = await reader.readexactly(length)
        text = body.decode()
        if text.lstrip().startswith("<"):
            return {"request": "998"}
        return json.loads(text)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connections += 1
        self.writers.append(writer)
        try:
            await self._read_frame(reader)  # login
            writer.write(make_login_block())
            await writer.drain()

            while True:
                message = await self._read_frame(reader)
                request = int(message["request"])

                if self.drop_next:
                    self.drop_next = False
                    writer.close()
                    return

                if request == 26:
                    continue
                status = self.status_for.get(request, 0)
                if status:
                    writer.write(reply(request, None, status))
                elif request == 15:
                    writer.write(reply(15, [{"ProductName": "VIARK SAT 4K"}]))
                elif request == 3:
                    writer.write(reply(3, [{"Data": "00001234567890"}]))
                else:
                    writer.write(reply(request, None))
                await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError, OSError):
            pass
        finally:
            with contextlib.suppress(Exception):
                writer.close()


@pytest.fixture
async def receiver():
    stub = StubReceiver()
    await stub.start()
    yield stub
    await stub.stop()


@pytest.mark.asyncio
async def test_login_and_request(receiver):
    client = ViarkClient("127.0.0.1", receiver.port)
    await client.connect()
    try:
        assert client.info["model"] == "VIARK SAT 4K"
        assert client.use_json is True
        result = await client.request(15)
        assert result[0]["ProductName"] == "VIARK SAT 4K"
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_non_zero_status_raises(receiver):
    receiver.status_for[1000] = 17  # receiver is showing a menu
    client = ViarkClient("127.0.0.1", receiver.port)
    await client.connect()
    try:
        with pytest.raises(ViarkRequestError) as err:
            await client.switch_channel("00001234567890")
        assert "menu" in str(err.value)
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_dropped_connection_is_reported_then_healed(receiver):
    client = ViarkClient("127.0.0.1", receiver.port, timeout=5)
    await client.connect()
    try:
        assert receiver.connections == 1

        receiver.drop_next = True
        with pytest.raises(ViarkConnectionError):
            await client.request(15)

        # The dead socket must not still look usable.
        assert client.connected is False

        # The next request should transparently reconnect.
        result = await client.request(15)
        assert result[0]["ProductName"] == "VIARK SAT 4K"
        assert receiver.connections == 2
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_concurrent_connects_open_a_single_socket(receiver):
    """connect() must be serialised, not merely idempotent-looking.

    Every caller checks self.connected and then awaits, so without a lock they all
    pass the check before any of them assigns self._writer. Each opens a socket,
    the last assignment wins, and the rest are leaked -- each one still holding a
    client slot the receiver will not hand back.
    """
    client = ViarkClient("127.0.0.1", receiver.port, timeout=5)
    try:
        await asyncio.gather(*(client.connect() for _ in range(5)))
        assert receiver.connections == 1
        assert client.connected is True
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_concurrent_requests_heal_a_drop_with_one_socket(receiver):
    """The real-world shape: two callers reconnecting after the same drop."""
    client = ViarkClient("127.0.0.1", receiver.port, timeout=5)
    await client.connect()
    try:
        assert receiver.connections == 1

        receiver.drop_next = True
        with pytest.raises(ViarkConnectionError):
            await client.request(15)
        assert client.connected is False

        # A coordinator refresh and a user action arriving together. Different
        # request types, since replies are matched by type alone.
        info, playing = await asyncio.gather(client.request(15), client.request(3))

        assert receiver.connections == 2, "the drop should heal with one new socket"
        assert info[0]["ProductName"] == "VIARK SAT 4K"
        assert playing[0]["Data"] == "00001234567890"
    finally:
        await client.disconnect()


class ExplodingWriter:
    """A StreamWriter whose drain() fails, as a socket dying mid-write does.

    Closing the peer is not enough to force this: TCP buffers the first write and
    only reports the failure on a later one, which makes the timing of a real
    socket test a coin flip. Failing at the writer keeps it deterministic and
    exercises the same except branch.
    """

    def __init__(self, inner: asyncio.StreamWriter) -> None:
        self._inner = inner

    def write(self, data: bytes) -> None:
        """Accept the bytes and drop them; the failure surfaces from drain()."""

    async def drain(self) -> None:
        raise ConnectionResetError("broken pipe")

    def is_closing(self) -> bool:
        return False

    def close(self) -> None:
        self._inner.close()

    async def wait_closed(self) -> None:
        with contextlib.suppress(Exception):
            await self._inner.wait_closed()


@pytest.mark.asyncio
async def test_write_failure_raises_a_viark_error(receiver):
    """Entity handlers catch ViarkError; a raw OSError would escape as a traceback."""
    client = ViarkClient("127.0.0.1", receiver.port, timeout=5)
    await client.connect()
    try:
        client._writer = ExplodingWriter(client._writer)

        with pytest.raises(ViarkConnectionError) as err:
            await client.request(15)
        assert isinstance(err.value, ViarkError)

        # The failed socket must not still look usable, or the next request is
        # written into it and waits out its timeout instead of reconnecting.
        assert client.connected is False
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_write_failure_does_not_orphan_its_own_future(receiver, caplog):
    """The failing request must consume the exception _fail_all() set on it.

    request() registers its waiter before writing, so tearing the connection down
    inside _write() fails that waiter too -- and this task never awaits it, having
    raised out of _write() first. Python then reports it when the future is
    collected, which is noise in every user's log.
    """
    client = ViarkClient("127.0.0.1", receiver.port, timeout=5)
    await client.connect()
    try:
        client._writer = ExplodingWriter(client._writer)

        with caplog.at_level(logging.ERROR, logger="asyncio"):
            with pytest.raises(ViarkConnectionError):
                await client.request(15)
            # The report happens when the future is collected, not when it fails.
            gc.collect()
            await asyncio.sleep(0)

        assert "never retrieved" not in caplog.text, caplog.text
    finally:
        await client.disconnect()


@pytest.mark.asyncio
async def test_notifications_are_dispatched_not_returned(receiver):
    seen: list[int] = []
    client = ViarkClient("127.0.0.1", receiver.port, on_notification=seen.append)
    await client.connect()
    try:
        # Push a notification from the receiver side.
        receiver.writers[-1].write(reply(2001, None))
        await receiver.writers[-1].drain()
        await asyncio.sleep(0.2)
        assert 2001 in seen
    finally:
        await client.disconnect()
