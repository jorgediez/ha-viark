"""Dump raw bytes for one request, with no interpretation.

Used to discover the wire format of responses that are not zlib-compressed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import sys
import time

#: Receiver address. Set VIARK_HOST, or pass --host explicitly.
HOST = os.environ.get("VIARK_HOST")
PORT = 20000

HELLO = (
    b"<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"
    b'<Command request="998" />'
)


def frame(p: bytes) -> bytes:
    return b"Start" + f"{len(p):07d}".encode() + b"End" + p


def dump(data: bytes) -> None:
    print(f"  total {len(data)} bytes")
    for off in range(0, min(len(data), 512), 16):
        chunk = data[off:off + 16]
        hexs = " ".join(f"{b:02x}" for b in chunk).ljust(47)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        print(f"    {off:04x}  {hexs}  {text}")
    if len(data) > 512:
        print(f"    ... {len(data) - 512} more bytes")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=HOST, required=HOST is None,
                    help="receiver IP address (or set VIARK_HOST)")
    ap.add_argument("--json", default=None, help="JSON body, e.g. '{\"request\":\"1009\"}'")
    ap.add_argument("--xml", default=None, help="raw XML body")
    ap.add_argument("--wait", type=float, default=6.0)
    args = ap.parse_args()

    sock = socket.create_connection((args.host, PORT), timeout=10)
    sock.sendall(frame(HELLO))
    time.sleep(1.5)
    sock.settimeout(1.0)
    # drain the hello response
    try:
        while sock.recv(65536):
            break
    except socket.timeout:
        pass

    if args.json:
        body = json.dumps(json.loads(args.json), separators=(",", ":")).encode()
    elif args.xml:
        body = args.xml.encode()
    else:
        print("need --json or --xml")
        return 1

    print(f">>> sending {body!r}")
    sock.sendall(frame(body))

    chunks = []
    deadline = time.time() + args.wait
    while time.time() < deadline:
        try:
            data = sock.recv(65536)
        except socket.timeout:
            continue
        if not data:
            print("  (closed by box)")
            break
        chunks.append(data)
        print(f"  + chunk {len(data)} bytes")

    sock.close()
    print()
    dump(b"".join(chunks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
