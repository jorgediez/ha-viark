"""Interactive keymap builder: run this while standing at the TV.

Automated scanning found only the keys whose effect shows up in the receiver's
readable state (channel, mute, power). Navigation keys, digits, colour buttons and
menus have no machine-visible effect, so they need a human to look at the screen.

For each code it counts down, sends the key, then asks what happened. Answers are
appended to a JSON file as you go, so the session can be stopped and resumed.

    python tools/map_keys_guided.py --start 3 --end 40 --out keymap.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "viark"))

from protocol import ViarkClient  # noqa: E402

#: Receiver address. Set VIARK_HOST, or pass --host explicitly.
DEFAULT_HOST = os.environ.get("VIARK_HOST")
KEY_EXIT = 7


async def ainput(prompt: str) -> str:
    """Read a line without blocking the event loop."""
    return (await asyncio.to_thread(input, prompt)).strip()


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=DEFAULT_HOST, required=DEFAULT_HOST is None,
                    help="receiver IP address (or set VIARK_HOST)")
    ap.add_argument("--start", type=int, default=3)
    ap.add_argument("--end", type=int, default=40)
    ap.add_argument("--countdown", type=float, default=3.0)
    ap.add_argument("--out", default="keymap.json")
    args = ap.parse_args()

    out_path = Path(args.out)
    keymap: dict[str, str] = {}
    if out_path.exists():
        keymap = json.loads(out_path.read_text("utf-8"))
        print(f"resuming: {len(keymap)} codes already recorded")

    print(
        "\nFor each code: watch the TV, then type what the button did.\n"
        "  Shortcuts: <enter> = nothing happened, 's' = skip,\n"
        "             'x' = send EXIT first then retry, 'q' = quit and save.\n"
    )

    async with ViarkClient(args.host) as client:
        for code in range(args.start, args.end + 1):
            if str(code) in keymap:
                continue

            while True:
                for remaining in range(int(args.countdown), 0, -1):
                    print(f"  code {code}: sending in {remaining}s ...", flush=True)
                    await asyncio.sleep(1.0)
                await client.send_key(code)
                print(f"  code {code}: SENT -- look at the TV")

                answer = await ainput(f"  what did code {code} do? ")
                if answer.lower() == "q":
                    out_path.write_text(json.dumps(keymap, indent=2), "utf-8")
                    print(f"\nsaved {len(keymap)} codes to {out_path}")
                    return 0
                if answer.lower() == "x":
                    await client.send_key(KEY_EXIT)
                    await asyncio.sleep(1.5)
                    print("  sent EXIT; retrying this code")
                    continue
                if answer.lower() == "s":
                    break

                keymap[str(code)] = answer or "no effect"
                out_path.write_text(json.dumps(keymap, indent=2), "utf-8")
                break

    out_path.write_text(json.dumps(keymap, indent=2), "utf-8")
    print(f"\nsaved {len(keymap)} codes to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
