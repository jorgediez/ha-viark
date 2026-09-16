# Viark Satellite Receiver — Home Assistant integration

[![hacs][hacs-badge]][hacs-url]
[![license][license-badge]](LICENSE)

Local control of **Viark** satellite receivers from Home Assistant, over the
receiver's own LAN protocol. No cloud, no polling of a web UI — the receiver
pushes state changes and the integration reacts.

Developed and verified against a **Viark SAT 4K**, platform id 140.
It should also work with other receivers speaking the same "G-MScreen" protocol
(many ALi, GX, HiSilicon and MStar based boxes — Viark, GTMedia, Freesat,
Starsat and similar), though only the SAT 4K has been tested.

> **Not Enigma2.** These boxes do not run Enigma2, so Home Assistant's built-in
> `enigma2` / OpenWebif integration does not work with them. That is why this
> integration exists.

For an on-screen remote to go with it, see the companion
[**ha-viark-remote-card**][remote-card].

## Features

| Capability | Implementation |
|---|---|
| Auto-discovery on the LAN | receiver broadcasts on UDP 25860 |
| Power on / off (standby) | request 1041 |
| Mute and unmute | key 23, state read via request 19 |
| Volume up / down | keys 35 / 36 |
| **Direct channel selection** | request 1000 — jumps straight to any channel |
| Channel up / down | keys 69 / 70, the receiver's own CH+/CH− |
| Current channel and on-screen number | request 3 |
| Full channel list | request 0, paged and cached |
| Satellite list | request 22 |
| Any remote key, by name or raw code | request 1040 |
| Push updates when the receiver changes, typically within a second | notifications 2001–2019 |
| Diagnostic entities (identity, capabilities) | login block + request 15 |

### Known limits

* **Deep standby cannot be woken.** The receiver leaves the network entirely, so
  nothing over IP can reach it. `turn_on` works only from *soft* standby. Use an
  IR blaster if you need a cold start.
* **Volume is step-only.** The receiver reports mute state but no volume level.
* **The receiver limits concurrent clients.** If the G-MScreen phone app is
  connected, Home Assistant may be refused with "receiver has no free client
  slot".
* **Changing channel fails while a menu is open on the TV** — the receiver
  returns status 17, surfaced as a readable error.

## Installation

Requires **Home Assistant 2025.3 or newer** — that release added
`AddConfigEntryEntitiesCallback`, which the platforms are typed against. There are
no external Python dependencies.

### HACS (custom repository)

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/jorgediez/ha-viark` as an **Integration**
3. Install **Viark Satellite Receiver**, then restart Home Assistant

### Manual

Copy `custom_components/viark/` into your Home Assistant
`config/custom_components/` directory and restart. There are no external
dependencies.

### Configuration

*Settings → Devices & Services → Add Integration → Viark*.

The form pre-fills the address of any receiver it hears broadcasting on the LAN,
so you normally just confirm. If Home Assistant runs in a container without host
networking it will not hear the broadcast — enter the IP manually. Receivers are
de-duplicated by serial number, so re-adding after an IP change updates the
existing entry instead of creating a duplicate.

## Entities

* **`media_player`** — power, mute, volume step, channel up/down, and
  `select_source` over the full channel list. In soft standby it reports **`off`**;
  `idle` means powered up but reporting no channel.
* **`remote`** — `remote.send_command` with named keys or raw codes.
* **Diagnostic sensors** — see below.

### The source list

Channels appear in the dropdown numbered, matching what the receiver shows
on screen:

```
0001 News HD
0002 News 2
...
0049 Sports HD
```

With a thousand-channel line-up that makes the list navigable, and it also
separates the **duplicate channel names** satellite line-ups routinely contain —
identical names were previously impossible to tell apart, and only the first was
reachable. Numbers are zero padded so the list stays in order even if the
frontend sorts it as text.

This is presentation only: tuning still uses the channel's internal `ServiceID`.
`select_source` accepts any of three forms, so **existing automations keep
working unchanged**:

| Input | Example |
|---|---|
| A label from the dropdown | `0049 Sports HD` |
| A bare channel name | `News HD` |
| A bare channel number | `49` |

A real channel name always wins over a channel number, so a channel actually
called "2" is still reachable by name. `media_title` stays the plain name
without the number, and `media_channel` reports the number on its own.

### Diagnostic entities

The receiver's login reply is a 108-byte block carrying much more identity than
setup needs, so the interesting parts are exposed as diagnostic entities. They
are grouped under the device and hidden from the main dashboard.

Enabled by default:

| Entity | Source |
|---|---|
| Serial number | request 15, falling back to the login block |
| Software version | request 15 |
| IP address | login block (the address the receiver believes it has) |
| Platform ID | login block — the chipset family, useful when reporting bugs |
| Channel count | request 15 |
| Receiver clock | receiver's own clock, handy for spotting a wrong time |
| Satellite menu | login block capability flag |

Registered but **disabled by default** — enable them in the entity settings if
you are debugging or reporting an issue against another receiver model:

`Data format` (JSON or XML) · `CPU chip ID` · `Flash ID` · `Customer ID` ·
`Model ID` · `Software version (raw)` · `Software sub-version` ·
`Maximum channels` · `SAT>IP mode` · `Client type`

Two caveats worth knowing:

* The login block is read **once per connection**, so those values only change
  when the integration reconnects. That is correct for what they describe —
  they are hardware identity, not live state.
* `SAT>IP mode` and `Client type` are raw numbers rather than yes/no. The two
  reverse-engineering sources describe those flag bits differently, so the value
  is passed through instead of being given a meaning that might be inverted.
* Some receivers report zeros for `Flash ID`. The SAT 4K used for development
  does.

The login block's "receiver full" bit is deliberately **not** exposed. The
client refuses to finish logging in when it is set, so for any connected client
it would be permanently false.

## Services

```yaml
# Press a named key
action: viark.send_key
target:
  entity_id: media_player.viark_sat_4k
data:
  key: epg

# Tune to a channel. A dropdown label ("0049 Sports HD"), a bare name,
# or a bare channel number all work.
action: media_player.select_source
target:
  entity_id: media_player.viark_sat_4k
data:
  source: "News HD"

# Type a channel number with the digit keys
action: remote.send_command
target:
  entity_id: remote.viark_sat_4k_remote
data:
  command: [digit_1, digit_2, digit_8]

# A raw code outside the verified table
action: viark.send_key
target:
  entity_id: media_player.viark_sat_4k
data:
  key: "82"
```

Named keys: `up` `down` `left` `right` `ok` `menu` `exit` `back` `red` `green`
`yellow` `blue` `digit_0`…`digit_9` `tv_radio` `mute` `recall` `satellite`
`subtitle` `epg` `favourite` `teletext` `volume_up` `volume_down` `page_up`
`page_down` `find` `power` `usb` `audio` `freeze` `resolution` `timer` `f1` `f2`
`info` `record` `rewind` `fast_forward` `play` `stop` `pause` `previous` `next`
`channel_up` `channel_down`.

`freeze` is worth knowing about: it stops the picture and the sound where they
are, and sending it again — or `exit` — returns to live. **No button on the
physical remote does this**, so it is something the integration can do that the
remote cannot. The receiver reports nothing while frozen, so the media player
still reads `playing`; don't build an automation that depends on detecting it.

`pause` (63) is the remote's Pause button and acts on USB media playback, which is
a different key from `freeze` (55).

Run `python tools/viark_cli.py keys` for the table with codes.

## Companion dashboard card

[**ha-viark-remote-card**][remote-card] is a custom Lovelace card that draws an
on-screen remote in the style of the receiver's physical one and drives it through
this integration. If you would rather press buttons than write `send_key` calls,
start there — installation and configuration are documented in that repository.

It is a separate project with its own release cycle; this integration does not
require it, and the card needs this integration installed to have anything to
talk to. The named keys listed above are what the card sends, so anything the
card can do is also reachable from an automation.

## Icons

Entity and service icons ship in `icons.json` and appear as soon as the
integration loads.

The **brand tile** in *Settings → Devices & Services* is served from
`custom_components/viark/brand/`. Since Home Assistant **2026.3** an integration
can carry its own brand images and they override the CDN automatically — no
configuration, and no pull request to the [brands repository][brands]. On older
releases the tile falls back to the default placeholder; everything else works
regardless.

```
custom_components/viark/brand/
├── icon.png      256x256
└── icon@2x.png   512x512
```

The artwork is a **generic satellite dish, not the Viark logo**. A community
integration should not imply an official association, and shipping a
manufacturer's trademark would do exactly that. No `logo.png` is included for the
same reason — that slot is a brand wordmark, which is not ours to invent.

Regenerate with `python tools/make_brand_images.py` (needs `pillow`), or simply
replace the PNGs. `tests/test_brand_images.py` checks size, squareness,
transparency and filenames.

## Protocol

The receiver speaks an undocumented protocol on TCP 20000. It is described in
full in **[PROTOCOL.md](PROTOCOL.md)** — framing, the obfuscated login block,
reply headers, request numbers, status codes and the remote key table.

That document was assembled by cross-referencing **two independent
reverse-engineering efforts** — one of the GMScreen Android app, one of the
PC-GMScreen Java client — and treating only details they agree on as
established. Everything was then verified against real hardware. Where the two
sources conflict (for example the meaning of notification 2014), the conflict is
recorded and the detail is not relied upon — unless hardware settles it, as
happened with key codes 55 and 63.

## Development

The tools talk to a receiver directly, without Home Assistant. Set `VIARK_HOST`
or pass `--host`:

```bash
export VIARK_HOST=192.168.1.50

python tools/viark_cli.py discover              # listen on UDP 25860
python tools/viark_cli.py info                  # receiver state
python tools/viark_cli.py now                   # current channel
python tools/viark_cli.py channels --start 0 --end 20
python tools/viark_cli.py tune "News HD"           # direct tune by name
python tools/viark_cli.py key mute
python tools/viark_cli.py keys                  # key alias table

python tools/verify_protocol.py                 # re-check protocol claims
python tools/test_actions.py                    # self-verifying tune + mute
python tools/map_keys_guided.py --start 24 --end 56 --out keymap.json
python tools/raw_capture.py --json '{"request":"14"}'
python tools/ha_import_check.py                 # import against a real HA install
python tools/make_brand_images.py               # regenerate the brand icons
```

### Tests

```bash
pip install pytest pytest-asyncio pytest-timeout pyyaml
python -m pytest tests/ -q
```

122 tests, no hardware required. They cover framing, compact-JSON encoding, XML
encoding, login-block decoding, reply-header layout, status codes, reconnection
against a stub receiver (including concurrent reconnects and write failures),
refresh pacing (the push cooldown, re-reading when the receiver pushes mid-fetch,
and a refused channel lookup), the diagnostic entity definitions, source-list
labelling and channel resolution, and the key table — including a guard that a
single-source code is never presented as verified unless it has been confirmed on
hardware, that `freeze` and `pause` never drift onto each other's code, and that
every entity has both a translated name and an icon, with no orphans left behind
when one is removed.

## Contributing

Key codes 25, 27, 28, 40, 41, 46–53, 56, 66–68 and 71–82 appear in only one of
the two reverse-engineering sources and have not been pressed on real hardware,
so they are deliberately not aliased. If you map any of them —
`tools/map_keys_guided.py` helps — a PR adding them to `KEY_ALIASES` is welcome.
Name them after the label on your remote rather than the one in
[PROTOCOL.md](PROTOCOL.md): where the two have differed, the remote was right.

Eight codes have already made that trip (24, 26, 44, 45, 54, 55, 69, 70) and are
recorded in PROTOCOL.md with the behaviour observed.

Reports from other receiver models are especially useful: the login block
reports a platform id, and behaviour is known to vary by platform.

## Credits

* Two reverse-engineering write-ups of the GMScreen Android app and the
  PC-GMScreen Java client, which supplied the request and key tables.
* [gabonator's ABcom set-top box notes][gabonator] — the original public
  description of the framing and the obfuscated login block.
* [PC-GMScreen][pcgmscreen], which bundles the Java client those notes build on.

## License

[MIT](LICENSE)

[remote-card]: https://github.com/jorgediez/ha-viark-remote-card
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[brands]: https://github.com/home-assistant/brands
[gabonator]: https://gist.github.com/gabonator/2c8885127cf6e0954c24e5d698ff99b6
[pcgmscreen]: https://github.com/adamlahbib/PC-GMScreen
