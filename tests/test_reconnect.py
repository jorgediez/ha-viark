"""Reconnection behaviour against a stub receiver.

Runs a minimal fake receiver in-process so the failure paths can be exercised
without the real hardware: a dropped connection must be noticed, reported to any
waiter, and healed on the next request.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
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
