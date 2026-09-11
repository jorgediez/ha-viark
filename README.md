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

## Features

| Capability | Implementation |
|---|---|
| Auto-discovery on the LAN | receiver broadcasts on UDP 25860 |
| Power on / off (standby) | request 1041 |
| Mute and unmute | key 23, state read via request 19 |
| Volume up / down | keys 35 / 36 |
| **Direct channel selection** | request 1000 — jumps straight to any channel |
| Channel up / down | keys 1 / 2 |
| Current channel and on-screen number | request 3 |
| Full channel list | request 0, paged and cached |
| Satellite list | request 22 |
| Any remote key, by name or raw code | request 1040 |
| Push updates when the receiver changes | notifications 2001–2019 |

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
  `select_source` over the full channel list.
* **`remote`** — `remote.send_command` with named keys or raw codes.

## Services

```yaml
# Press a named key
action: viark.send_key
target:
  entity_id: media_player.viark_sat_4k
data:
  key: epg

# Tune to a channel by name
action: media_player.select_source
target:
  entity_id: media_player.viark_sat_4k
data:
  source: "LA 1"

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
`page_down` `find` `power` `usb` `info` `record` `rewind` `fast_forward` `play`
`stop` `pause` `previous` `next` `channel_up` `channel_down`.

Run `python tools/viark_cli.py keys` for the table with codes.

## Protocol

The receiver speaks an undocumented protocol on TCP 20000. It is described in
full in **[PROTOCOL.md](PROTOCOL.md)** — framing, the obfuscated login block,
reply headers, request numbers, status codes and the remote key table.

That document was assembled by cross-referencing **two independent
reverse-engineering efforts** — one of the GMScreen Android app, one of the
PC-GMScreen Java client — and treating only details they agree on as
established. Everything was then verified against real hardware. Where the two
sources conflict (for example the meaning of notification 2014), the conflict is
recorded and the detail is not relied upon.

## Development

The tools talk to a receiver directly, without Home Assistant. Set `VIARK_HOST`
or pass `--host`:

```bash
export VIARK_HOST=192.168.1.50

python tools/viark_cli.py discover              # listen on UDP 25860
python tools/viark_cli.py info                  # receiver state
python tools/viark_cli.py now                   # current channel
python tools/viark_cli.py channels --start 0 --end 20
python tools/viark_cli.py tune "LA 1"           # direct tune by name
python tools/viark_cli.py key mute
python tools/viark_cli.py keys                  # key alias table

python tools/verify_protocol.py                 # re-check protocol claims
python tools/test_actions.py                    # self-verifying tune + mute
python tools/map_keys_guided.py --start 24 --end 56 --out keymap.json
python tools/raw_capture.py --json '{"request":"14"}'
python tools/ha_import_check.py                 # import against a real HA install
```

### Tests

```bash
pip install pytest pytest-asyncio pytest-timeout
python -m pytest tests/ -q
```

36 tests, no hardware required. They cover framing, compact-JSON encoding, XML
encoding, login-block decoding, reply-header layout, status codes, reconnection
against a stub receiver, and the key table — including a guard that key codes
documented by only one source are never presented as verified.

## Contributing

Key codes 24–28, 40, 41, 44–56 and 66–82 appear in only one of the two
reverse-engineering sources and are deliberately not aliased. If you map any of
them on real hardware — `tools/map_keys_guided.py` helps — a PR adding them to
`KEY_ALIASES` is welcome.

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

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[gabonator]: https://gist.github.com/gabonator/2c8885127cf6e0954c24e5d698ff99b6
[pcgmscreen]: https://github.com/adamlahbib/PC-GMScreen
