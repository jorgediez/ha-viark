"""Command-line harness for the Viark receiver.

Usage:
    python tools/viark_cli.py info
    python tools/viark_cli.py now
    python tools/viark_cli.py channels --start 45 --end 55
    python tools/viark_cli.py tune "Sports 2 HD"
    python tools/viark_cli.py key mute
    python tools/viark_cli.py key 1 --watch --delay 10
    python tools/viark_cli.py discover
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "viark"))

from const import KEY_ALIASES  # noqa: E402
from protocol import ViarkClient, async_discover  # noqa: E402

#: Receiver address. Set VIARK_HOST, or pass --host explicitly.
DEFAULT_HOST = os.environ.get("VIARK_HOST")


def resolve(token: str) -> int:
    key = token.strip().lower()
    if key in KEY_ALIASES:
        return KEY_ALIASES[key]
    return int(key)


def describe(channel: dict | None) -> str:
    if not channel:
        return "<nothing playing>"
    index = channel.get("ServiceIndex")
    # The receiver counts from 0 but the on-screen number starts at 1.
    on_screen = index + 1 if isinstance(index, int) else "?"
    return (
        f"index {index} / on-screen {on_screen} -- {channel.get('ServiceName')!r} "
        f"(ServiceID {channel.get('ServiceID')})"
    )


async def current(client: ViarkClient) -> dict | None:
    program_id = await client.playing_program_id()
    if not program_id:
        return None
    for ch in await client.channels():
        if ch.get("ServiceID") == program_id:
            return ch
    return {"ServiceID": program_id}


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST, required=DEFAULT_HOST is None,
                        help="receiver IP address (or set VIARK_HOST)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info")
    sub.add_parser("now")
    sub.add_parser("sats")
    sub.add_parser("keys")

    p_disc = sub.add_parser("discover")
    p_disc.add_argument("--seconds", type=float, default=8.0)

    p_key = sub.add_parser("key")
    p_key.add_argument("codes", nargs="+")
    p_key.add_argument("--watch", action="store_true")
    p_key.add_argument("--delay", type=float, default=0.0)

    p_tune = sub.add_parser("tune")
    p_tune.add_argument("name")

    p_raw = sub.add_parser("raw")
    p_raw.add_argument("request", type=int)

    p_chan = sub.add_parser("channels")
    p_chan.add_argument("--start", type=int, default=0)
    p_chan.add_argument("--end", type=int, default=9)

    args = parser.parse_args()

    if args.cmd == "keys":
        for name, code in sorted(KEY_ALIASES.items(), key=lambda kv: (kv[1], kv[0])):
            print(f"  {code:3}  {name}")
        return 0

    if args.cmd == "discover":
        print(f"listening on UDP 25860 for {args.seconds:.0f}s ...")
        found = await async_discover(args.seconds)
        if not found:
            print("  no receivers broadcast (they announce every few seconds)")
        for ip, info in found.items():
            print(f"  {ip}  {info['model']}  serial {info['serial']}  "
                  f"platform {info['platform_id']}  "
                  f"{'JSON' if info['use_json'] else 'XML'}")
        return 0

    async with ViarkClient(args.host, client_name="viark-cli") as client:
        print(f"connected: {client.info['model']} "
              f"(platform {client.info['platform_id']}, "
              f"{'JSON' if client.use_json else 'XML'})\n")

        if args.cmd == "info":
            for key, value in (await client.state()).items():
                if key != "FavGroupNames":
                    print(f"  {key:24} {value}")

        elif args.cmd == "now":
            print("  playing:", describe(await current(client)))

        elif args.cmd == "sats":
            for sat in await client.satellites():
                print(f"  [{sat['SatIndex']:2}] {sat['SatName']}")

        elif args.cmd == "channels":
            playing = await client.playing_program_id()
            for ch in await client.channels(args.start, args.end):
                flag = " <== PLAYING" if ch.get("ServiceID") == playing else ""
                print(f"  #{ch['ServiceIndex']:4} {ch['ServiceName']}{flag}")

        elif args.cmd == "tune":
            target = next(
                (c for c in await client.channels()
                 if c.get("ServiceName") == args.name),
                None,
            )
            if not target:
                print(f"  no channel named {args.name!r}")
                return 1
            print(f"  tuning to {describe(target)}")
            await client.switch_channel(target["ServiceID"], int(target.get("Radio", 0)))
            await asyncio.sleep(3.0)
            print("  now:", describe(await current(client)))

        elif args.cmd == "key":
            if args.watch:
                print("  before:", describe(await current(client)))
            for remaining in range(int(args.delay), 0, -1):
                print(f"  sending in {remaining:2}s ...", flush=True)
                await asyncio.sleep(1.0)
            for code in args.codes:
                resolved = resolve(code)
                print(f"  >>> sending {code} (KeyValue={resolved}) NOW", flush=True)
                await client.send_key(resolved)
                await asyncio.sleep(1.5)
            if args.watch:
                await asyncio.sleep(2.0)
                print("  after: ", describe(await current(client)))

        elif args.cmd == "raw":
            print(json.dumps(await client.request(args.request), indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
