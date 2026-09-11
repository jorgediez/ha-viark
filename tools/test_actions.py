"""Verify the action commands the two reverse-engineering documents agree on.

Two self-verifying round trips, both harmless and both restored afterwards:

* request 1000 -- tune to another channel and back, confirmed with request 3.
* key 23 (mute) -- toggle and untoggle, confirmed with request 19.

Passing the mute test validates the shared key table, since 23 is only "mute"
because both documents say so.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "viark"))

from protocol import ViarkClient, ViarkError  # noqa: E402

#: Receiver address. Set VIARK_HOST, or pass --host explicitly.
DEFAULT_HOST = os.environ.get("VIARK_HOST")
KEY_MUTE = 23
SETTLE = 3.0


async def name_of(client: ViarkClient, program_id: str | None, channels) -> str:
    if not program_id:
        return "<none>"
    for ch in channels:
        if ch.get("ServiceID") == program_id:
            return f"#{ch.get('ServiceIndex')} {ch.get('ServiceName')}"
    return f"<unknown {program_id}>"


async def test_switch(client: ViarkClient, target_index: int) -> bool:
    print("\n=== request 1000: direct channel switch ===")
    channels = await client.channels(0, 99)
    start_id = await client.playing_program_id()
    print(f"  before: {await name_of(client, start_id, channels)}")

    target = next(
        (c for c in channels if c.get("ServiceIndex") == target_index), None
    )
    if not target or target.get("ServiceID") == start_id:
        print("  cannot pick a distinct target channel; skipping")
        return False

    print(f"  tuning to #{target['ServiceIndex']} {target['ServiceName']} ...")
    try:
        await client.switch_channel(target["ServiceID"], int(target.get("Radio", 0)))
    except ViarkError as exc:
        print(f"  [FAIL] receiver refused: {exc}")
        return False

    await asyncio.sleep(SETTLE)
    now = await client.playing_program_id()
    print(f"  after:  {await name_of(client, now, channels)}")
    ok = now == target["ServiceID"]
    print("  [ OK ] direct tune works" if ok else "  [FAIL] channel did not change")

    if start_id and now != start_id:
        print("  restoring original channel ...")
        await client.switch_channel(start_id)
        await asyncio.sleep(SETTLE)
        back = await client.playing_program_id()
        print(f"  restored to: {await name_of(client, back, channels)}")
    return ok


async def test_mute(client: ViarkClient) -> bool:
    print("\n=== key 23: mute toggle (validates the shared key table) ===")
    before = await client.mute_state()
    print(f"  mute before: {before}")

    await client.send_key(KEY_MUTE)
    await asyncio.sleep(SETTLE)
    during = await client.mute_state()
    print(f"  mute after press: {during}")

    ok = before is not None and during is not None and during != before
    if ok:
        print("  [ OK ] key 23 toggles mute -- key table confirmed")
    else:
        print("  [FAIL] mute state did not change")

    # Always put it back, so the TV is not left silent.
    await client.send_key(KEY_MUTE)
    await asyncio.sleep(SETTLE)
    print(f"  mute restored to: {await client.mute_state()}")
    return ok


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=DEFAULT_HOST, required=DEFAULT_HOST is None,
                    help="receiver IP address (or set VIARK_HOST)")
    ap.add_argument("--target-index", type=int, default=52)
    args = ap.parse_args()

    async with ViarkClient(args.host) as client:
        print(f"connected: {client.info['model']} platform {client.info['platform_id']}")
        switched = await test_switch(client, args.target_index)
        muted = await test_mute(client)

    print("\n=== summary ===")
    print(f"  direct tune (1000): {'WORKS' if switched else 'FAILED'}")
    print(f"  mute key (23):      {'WORKS' if muted else 'FAILED'}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
