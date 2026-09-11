"""Asyncio client for the ALi / "G-MScreen" protocol used by Viark receivers.

The wire format below is taken from two independent reverse-engineering efforts --
the GMScreen Android app and the PC-GMScreen Java client -- and only details the
two agree on are relied upon here. See PROTOCOL.md for the cross-check.

Summary:

* Control channel is TCP 20000; receivers also broadcast their identity on
  UDP 25860.
* Requests are framed ``b"Start" + b"%07d" % len(body) + b"End" + body`` and are
  never compressed. The body is JSON or XML, chosen by the receiver at login.
* Replies and notifications share a 16-byte header::

      b"GCDH" + u32le(payload_len) + u32le(type) + u32le(status)

  ``payload_len == 0`` means there is no body -- action requests are commonly
  acknowledged this way. Any body is a zlib stream.
* Login is request 998, whose reply is 108 raw bytes (no GCDH header) obfuscated
  by reversing the buffer and XOR-ing every byte with 0x5b.
* Replies are matched to requests by ``type`` alone; there are no sequence ids, so
  at most one request per type may be outstanding.
* The receiver pushes 2000-2999 notifications when its state changes.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import socket
import struct
import zlib
from typing import Any, Callable
from xml.etree import ElementTree

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 20000
DISCOVERY_PORT = 25860

XML_DECL = "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"

LOGIN_BLOCK_LENGTH = 108
LOGIN_MAGIC = b"39WwijOog54a"
OBFUSCATION_KEY = 0x5B

ACK_MAGIC = b"GCDH"
ACK_LENGTH = 16

# --- request numbers (agreed by both sources) --------------------------------
REQ_CHANNEL_LIST = 0
REQ_PLAYING_CHANNEL = 3
REQ_STB_INFO = 15
REQ_MUTE_STATE = 19
REQ_SATELLITE_LIST = 22
REQ_KEEPALIVE = 26
REQ_LOGIN = 998
REQ_SWITCH_CHANNEL = 1000
REQ_STREAM_URL = 1009
REQ_STOP_STREAM = 1012
REQ_SEND_KEY = 1040
REQ_POWER = 1041

#: Firmware 1.32 answers request 14 with a merged blob covering what the
#: documentation attributes to several separate requests. Verified on hardware.
REQ_MERGED_STATE = 14

NOTIFICATION_RANGE = range(2000, 3000)
NOTIFY_PLAYING_CHANGED = 2001
NOTIFY_CHANNEL_LIST_CHANGED = 2002
NOTIFY_MUTE_CHANGED = 2003
NOTIFY_TV_RADIO_CHANGED = 2004

#: Result codes both sources agree on. Anything non-zero means the request failed.
STATUS_OK = 0
STATUS_MESSAGES = {
    1: "failed",
    2: "format error",
    3: "receiver out of memory",
    5: "receiver timed out",
    9: "wrong password",
    16: "channel is being recorded",
    17: "receiver is showing a menu",
}

#: Both sources cap a channel-list page at 100 records.
CHANNEL_PAGE_SIZE = 100

DEFAULT_TIMEOUT = 15.0

#: Sources disagree on the idle limit (30 s vs 60 s), so keep well inside both.
KEEPALIVE_INTERVAL = 10.0


class ViarkError(Exception):
    """Base class for Viark protocol failures."""


class ViarkConnectionError(ViarkError):
    """Could not connect to, or lost connection with, the receiver."""


class ViarkRequestError(ViarkError):
    """The receiver rejected a request with a non-zero status."""

    def __init__(self, request: int, status: int) -> None:
        self.request = request
        self.status = status
        detail = STATUS_MESSAGES.get(status, f"status {status}")
        super().__init__(f"request {request} failed: {detail}")


def frame(body: bytes) -> bytes:
    """Wrap a request body in the ``Start<length>End`` envelope."""
    return b"Start" + f"{len(body):07d}".encode() + b"End" + body


def deobfuscate(block: bytes) -> bytes:
    """Undo the login block's obfuscation (reverse, then XOR 0x5b)."""
    return bytes(b ^ OBFUSCATION_KEY for b in reversed(block))


def parse_login_block(block: bytes) -> dict[str, Any]:
    """Decode the 108-byte identity struct returned by request 998."""
    if len(block) != LOGIN_BLOCK_LENGTH:
        raise ViarkConnectionError(
            f"login block should be {LOGIN_BLOCK_LENGTH} bytes, got {len(block)}"
        )
    plain = deobfuscate(block)
    if plain[:12] != LOGIN_MAGIC:
        raise ViarkConnectionError("login block magic mismatch; not a G-MScreen receiver")

    serial_raw = plain[12:20]
    flags_a = plain[84]
    return {
        "serial": "%06d%06d"
        % (
            int.from_bytes(serial_raw[0:3], "big"),
            int.from_bytes(serial_raw[3:6], "big"),
        ),
        # NUL-terminated, and this firmware pads it with a trailing newline.
        "model": plain[20:52].split(b"\0")[0].decode("ascii", "replace").strip(),
        # Stored little-endian, so the dotted form reads back to front.
        "ip": ".".join(str(x) for x in plain[71:67:-1]),
        "platform_id": plain[72],
        "sw_version": int.from_bytes(plain[73:75], "big"),
        "customer_id": plain[75],
        "model_id": plain[76],
        "sw_sub_version": int.from_bytes(plain[80:84], "little"),
        "connected_full": bool(flags_a & 0x01),
        "sat_enable": bool(flags_a & 0x04),
        "use_json": bool(flags_a & 0x40),
    }


def _clean(value: Any) -> Any:
    """Strip the stray control bytes the receiver prefixes some strings with."""
    if isinstance(value, str):
        return value.strip("".join(chr(c) for c in range(0, 32))).strip()
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    return value


def _parse_xml_records(body: bytes) -> list[dict[str, Any]]:
    """Flatten an XML reply into the same shape the JSON parser produces."""
    root = ElementTree.fromstring(body.decode("utf-8", "replace"))
    records = [
        {child.tag: child.text for child in parm} for parm in root.iter("parm")
    ]
    if records:
        return records
    return [{child.tag: child.text for child in root}]


async def async_discover(timeout: float = 6.0) -> dict[str, dict[str, Any]]:
    """Listen for receiver broadcasts on UDP 25860.

    Receivers announce themselves; clients never probe. Returns a mapping of
    IP address to decoded identity.
    """
    loop = asyncio.get_running_loop()
    found: dict[str, dict[str, Any]] = {}

    class _Protocol(asyncio.DatagramProtocol):
        def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
            if len(data) != LOGIN_BLOCK_LENGTH:
                return
            try:
                found[addr[0]] = parse_login_block(data)
            except ViarkError:
                pass

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    with contextlib.suppress(AttributeError, OSError):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("", DISCOVERY_PORT))

    transport, _ = await loop.create_datagram_endpoint(_Protocol, sock=sock)
    try:
        await asyncio.sleep(timeout)
    finally:
        transport.close()
    return found


class ViarkClient:
    """One long-lived control connection to a receiver."""

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        client_name: str = "home-assistant",
        client_uuid: str = "home-assistant-viark",
        on_notification: Callable[[int], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client_name = client_name
        self.client_uuid = client_uuid
        self.on_notification = on_notification

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._keepalive_task: asyncio.Task[None] | None = None

        # Replies are matched by type alone, so one waiter per type.
        self._waiters: dict[int, asyncio.Future[Any]] = {}
        self._send_lock = asyncio.Lock()

        self.info: dict[str, Any] = {}
        self.use_json = True

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    # -- connection -----------------------------------------------------------

    async def connect(self) -> None:
        if self.connected:
            return

        # A previous session may have ended in the read loop; clear its tasks so
        # reconnecting does not leave a second keepalive running.
        for task in (self._keepalive_task, self._reader_task):
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._keepalive_task = None
        self._reader_task = None

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout=self.timeout
            )
        except (OSError, asyncio.TimeoutError) as exc:
            raise ViarkConnectionError(
                f"cannot connect to {self.host}:{self.port}: {exc}"
            ) from exc

        # Login is always XML: the data format is only known once it replies.
        login = (
            f"{XML_DECL}<Command request=\"{REQ_LOGIN}\">"
            f"<data>{self.client_name}</data><uuid>{self.client_uuid}</uuid></Command>"
        )
        try:
            self._writer.write(frame(login.encode("utf-8")))
            await self._writer.drain()
            block = await asyncio.wait_for(
                self._reader.readexactly(LOGIN_BLOCK_LENGTH), timeout=self.timeout
            )
        except (OSError, asyncio.IncompleteReadError, asyncio.TimeoutError) as exc:
            await self.disconnect()
            raise ViarkConnectionError(f"login failed: {exc}") from exc

        self.info = parse_login_block(block)
        if self.info["connected_full"]:
            await self.disconnect()
            raise ViarkConnectionError("receiver has no free client slot")

        self.use_json = self.info["use_json"]
        _LOGGER.debug(
            "connected to %s (%s, platform %s, %s)",
            self.host,
            self.info["model"],
            self.info["platform_id"],
            "JSON" if self.use_json else "XML",
        )

        self._reader_task = asyncio.create_task(self._read_loop())
        self._keepalive_task = asyncio.create_task(self._keepalive_loop())

    async def disconnect(self) -> None:
        for task in (self._keepalive_task, self._reader_task):
            if task:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._keepalive_task = None
        self._reader_task = None

        if self._writer:
            self._writer.close()
            with contextlib.suppress(Exception):
                await self._writer.wait_closed()
        self._reader = None
        self._writer = None
        self._fail_all(ViarkConnectionError("disconnected"))

    # -- receive --------------------------------------------------------------

    async def _read_loop(self) -> None:
        assert self._reader is not None
        try:
            while True:
                header = await self._reader.readexactly(ACK_LENGTH)
                if header[:4] != ACK_MAGIC:
                    raise ViarkConnectionError(f"bad frame header {header[:4]!r}")
                length, mtype, status = struct.unpack("<III", header[4:])

                body = b""
                if length:
                    raw = await self._reader.readexactly(length)
                    try:
                        body = zlib.decompress(raw)
                    except zlib.error as exc:
                        _LOGGER.warning("undecompressable body for type %s: %s", mtype, exc)
                        body = b""

                self._dispatch(mtype, status, body)
        except asyncio.CancelledError:
            raise
        except (asyncio.IncompleteReadError, ConnectionError, OSError) as exc:
            self._handle_connection_lost(f"connection lost: {exc}")
        except Exception as exc:  # noqa: BLE001 - surfaced to waiters
            _LOGGER.debug("read loop for %s ended: %s", self.host, exc)
            self._handle_connection_lost(str(exc))

    def _handle_connection_lost(self, reason: str) -> None:
        """Tear the socket down so the next request reconnects.

        Without this the writer can still look open after the read loop has died,
        so every later request would be written into a dead socket and time out
        instead of reconnecting.
        """
        _LOGGER.debug("connection to %s lost: %s", self.host, reason)
        if self._writer is not None:
            with contextlib.suppress(Exception):
                self._writer.close()
        self._reader = None
        self._writer = None
        self._fail_all(ViarkConnectionError(reason))

    def _dispatch(self, mtype: int, status: int, body: bytes) -> None:
        if mtype in NOTIFICATION_RANGE:
            _LOGGER.debug("notification %s from %s", mtype, self.host)
            if self.on_notification:
                self.on_notification(mtype)
            return

        future = self._waiters.pop(mtype, None)
        if future is None or future.done():
            return
        if status != STATUS_OK:
            future.set_exception(ViarkRequestError(mtype, status))
            return
        future.set_result(self._decode(body))

    def _decode(self, body: bytes) -> Any:
        if not body:
            return None
        try:
            if self.use_json:
                return _clean(json.loads(body.decode("utf-8", "replace")))
            return _clean(_parse_xml_records(body))
        except (json.JSONDecodeError, ElementTree.ParseError) as exc:
            _LOGGER.warning("could not parse reply from %s: %s", self.host, exc)
            return None

    def _fail_all(self, exc: Exception) -> None:
        for future in self._waiters.values():
            if not future.done():
                future.set_exception(exc)
        self._waiters.clear()

    # -- send -----------------------------------------------------------------

    def _encode(self, request: int, fields: dict[str, Any] | None) -> bytes:
        fields = fields or {}
        if self.use_json:
            body: dict[str, Any] = {"request": str(request)}
            body.update(fields)
            return json.dumps(body, separators=(",", ":")).encode("utf-8")

        inner = ""
        for key, value in fields.items():
            if key == "array":
                for item in value:
                    inner += "<parm>"
                    inner += "".join(f"<{k}>{v}</{k}>" for k, v in item.items())
                    inner += "</parm>"
            else:
                inner += f"<{key}>{value}</{key}>"
        if inner:
            return f'{XML_DECL}<Command request="{request}">{inner}</Command>'.encode()
        return f'{XML_DECL}<Command request="{request}" />'.encode()

    async def _write(self, request: int, fields: dict[str, Any] | None = None) -> None:
        if not self.connected:
            await self.connect()
        assert self._writer is not None
        async with self._send_lock:
            self._writer.write(frame(self._encode(request, fields)))
            await self._writer.drain()

    async def request(
        self,
        request: int,
        fields: dict[str, Any] | None = None,
        expect_reply: bool = True,
        timeout: float | None = None,
    ) -> Any:
        """Send a request and, unless told otherwise, wait for its reply."""
        if not self.connected:
            await self.connect()

        if not expect_reply:
            await self._write(request, fields)
            return None

        existing = self._waiters.get(request)
        if existing and not existing.done():
            raise ViarkError(f"a request of type {request} is already outstanding")

        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._waiters[request] = future
        try:
            await self._write(request, fields)
            return await asyncio.wait_for(future, timeout=timeout or self.timeout)
        except asyncio.TimeoutError as exc:
            raise ViarkError(f"timed out waiting for reply to {request}") from exc
        finally:
            self._waiters.pop(request, None)

    async def _keepalive_loop(self) -> None:
        """Hold the session open; the receiver drops idle clients."""
        try:
            while True:
                await asyncio.sleep(KEEPALIVE_INTERVAL)
                if not self.connected:
                    return
                with contextlib.suppress(ViarkError, OSError):
                    await self._write(REQ_KEEPALIVE)
        except asyncio.CancelledError:
            raise

    # -- high level -----------------------------------------------------------

    @staticmethod
    def _first(result: Any) -> dict[str, Any]:
        if isinstance(result, list) and result:
            return result[0] if isinstance(result[0], dict) else {}
        if isinstance(result, dict):
            return result
        return {}

    async def state(self) -> dict[str, Any]:
        """Read receiver state.

        Firmware 1.32 answers request 14 with a merged blob covering device info,
        clock, mute and lock settings. Falls back to request 15, which the two
        reference clients document as the info request.
        """
        try:
            merged = self._first(await self.request(REQ_MERGED_STATE))
            if merged:
                return merged
        except ViarkError as exc:
            _LOGGER.debug("merged state request failed on %s: %s", self.host, exc)
        return self._first(await self.request(REQ_STB_INFO))

    async def satellites(self) -> list[dict[str, Any]]:
        result = await self.request(REQ_SATELLITE_LIST)
        return result if isinstance(result, list) else []

    async def channels(self, start: int = 0, end: int | None = None) -> list[dict[str, Any]]:
        """Fetch channel records, paging within the 100-record limit."""
        if end is None:
            info = await self.state()
            end = int(info.get("ChannelNum", 0)) - 1

        out: list[dict[str, Any]] = []
        index = start
        while index <= end:
            stop = min(index + CHANNEL_PAGE_SIZE - 1, end)
            page = await self.request(
                REQ_CHANNEL_LIST, {"FromIndex": str(index), "ToIndex": str(stop)}
            )
            if not isinstance(page, list) or not page:
                break
            out.extend(page)
            index = stop + 1
        return out

    async def playing_program_id(self) -> str | None:
        """Ask the receiver which channel is on the TV (request 3)."""
        try:
            record = self._first(await self.request(REQ_PLAYING_CHANNEL))
        except ViarkError as exc:
            _LOGGER.debug("playing-channel request failed on %s: %s", self.host, exc)
            return None
        value = record.get("Data")
        return str(value) if value not in (None, "") else None

    async def mute_state(self) -> bool | None:
        try:
            record = self._first(await self.request(REQ_MUTE_STATE))
        except ViarkError:
            return None
        value = record.get("Data")
        return None if value is None else bool(int(value))

    async def send_key(self, *keys: int | str) -> None:
        """Inject remote key codes (request 1040). The receiver sends no reply."""
        for key in keys:
            await self.request(
                REQ_SEND_KEY,
                {"array": [{"KeyValue": str(key)}]},
                expect_reply=False,
            )

    async def switch_channel(self, program_id: str, tv_state: int = 0) -> None:
        """Tune directly to a channel (request 1000).

        ``tv_state`` is the channel record's ``Radio`` flag: 0 for TV, 1 for radio.
        """
        await self.request(
            REQ_SWITCH_CHANNEL,
            {"array": [{"TvState": str(tv_state), "ProgramId": str(program_id)}]},
        )

    async def power_toggle(self) -> None:
        """Toggle standby (request 1041)."""
        await self.request(REQ_POWER, expect_reply=False)

    async def __aenter__(self) -> ViarkClient:
        await self.connect()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.disconnect()
