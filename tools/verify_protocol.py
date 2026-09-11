"""Verify the cross-checked protocol against the live receiver.

Checks the claims the two reverse-engineering documents agree on, so the
integration is built on behaviour confirmed on this hardware rather than on
client-side code reading alone.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "viark"))

from protocol import (  # noqa: E402
    REQ_MUTE_STATE,
    REQ_PLAYING_CHANNEL,
    REQ_STB_INFO,
    ViarkClient,
    ViarkError,
)

#: Receiver address. Set VIARK_HOST, or pass --host explicitly.
DEFAULT_HOST = os.environ.get("VIARK_HOST")


async def check(label, coro):
    try:
        result = await coro
    except ViarkError as exc:
        print(f"  [FAIL] {label}: {exc}")
        return None
    print(f"  [ OK ] {label}: {result!r}"[:300])
    return result


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=DEFAULT_HOST, required=DEFAULT_HOST is None,
                    help="receiver IP address (or set VIARK_HOST)")
    args = ap.parse_args()

    async with ViarkClient(args.host) as client:
        print("=== login block (998) ===")
        for key, value in client.info.items():
            print(f"  {key:18} {value}")

        print("\n=== requests both documents describe ===")
        await check("15 STB info", client.request(REQ_STB_INFO))
        await check("3  playing channel", client.request(REQ_PLAYING_CHANNEL))
        await check("19 mute state", client.request(REQ_MUTE_STATE))

        print("\n=== helpers ===")
        await check("state()", client.state())
        await check("playing_program_id()", client.playing_program_id())
        await check("mute_state()", client.mute_state())

        print("\n=== channel paging (100 per page) ===")
        page = await client.channels(0, 4)
        for ch in page:
            print(f"  #{ch.get('ServiceIndex')} {ch.get('ServiceName')} "
                  f"id={ch.get('ServiceID')} radio={ch.get('Radio')}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
