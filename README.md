# Viark Satellite Receiver — Home Assistant integration

[![hacs][hacs-badge]][hacs-url]
[![release][release-badge]][release-url]
[![validate][validate-badge]][validate-url]
[![tests][tests-badge]][tests-url]
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

It comes with an on-screen [**remote card**](#remote-card) for your dashboards, a
button-for-button replica of the receiver's remote.

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
| [Remote card](#remote-card) for dashboards | ships with the integration, loaded automatically |

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

[![Open your Home Assistant instance and open this repository in HACS.][my-hacs-badge]][my-hacs-url]

Or by hand:

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/jorgediez/ha-viark` as an **Integration**
3. Install **Viark Satellite Receiver**, then restart Home Assistant

The [remote card](#remote-card) comes with it; there is nothing else to install.

### Manual

Copy `custom_components/viark/` into your Home Assistant
`config/custom_components/` directory and restart. There are no external
dependencies. The remote card is in that folder too, in `www/`.

### Configuration

[![Open your Home Assistant instance and start setting up Viark.][my-setup-badge]][my-setup-url]

Or *Settings → Devices & Services → Add Integration → Viark*.

The form pre-fills the address of any receiver it hears broadcasting on the LAN,
so you normally just confirm. If Home Assistant runs in a container without host
networking it will not hear the broadcast — enter the IP manually. Receivers are
de-duplicated by serial number, so re-adding after an IP change updates the
existing entry instead of creating a duplicate.

To change the address of a configured receiver, open it under *Settings →
Devices & Services → Viark*, then **⋮ → Reconfigure**. An address that answers
with a different receiver's serial number is refused.

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

## Actions

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

Run `python scripts/viark_cli.py keys` for the table with codes.

### Example automations

```yaml
# Start on the news when the receiver comes out of standby in the morning
triggers:
  - trigger: state
    entity_id: media_player.viark_sat_4k
    from: "off"
    to: playing
conditions:
  - condition: time
    after: "06:00:00"
    before: "10:00:00"
actions:
  - action: media_player.select_source
    target:
      entity_id: media_player.viark_sat_4k
    data:
      source: "News HD"

# Mute the TV while someone is at the door
triggers:
  - trigger: state
    entity_id: binary_sensor.doorbell
    to: "on"
actions:
  - action: media_player.volume_mute
    target:
      entity_id: media_player.viark_sat_4k
    data:
      is_volume_muted: true
```

Muting only sends the mute key when the receiver is not already muted, so the
second automation cannot unmute by accident.

## Remote card

The integration ships a dashboard card that looks and works like the receiver's
remote control. Every button of the physical remote is on the card, in the same
place.

<p align="center">
  <img src="https://raw.githubusercontent.com/jorgediez/ha-viark/main/images/remote-card.png" alt="The Viark remote card" width="320">
</p>

- Button-for-button replica of the original remote, scaled to any card width.
- Works with either the integration's `media_player` or `remote` entity.
- Status window with a power LED and the channel that is playing.
- **Hold to repeat** on volume, channel and arrow buttons, paced to what the
  receiver accepts. Scrolling the dashboard over the card never presses a key.
- Visual editor, card picker preview and sections view sizing.
- Every button can be remapped to a raw key code or any Home Assistant action.
- Haptic feedback in the companion app, keyboard navigation and screen reader
  labels.
- English and Spanish.

The integration loads the card into every dashboard, storage or YAML, as soon as
a receiver is set up. There is no dashboard resource to add. After an update,
reload the browser to get the new card. It does not load on Google Cast displays,
which only load dashboard resources.

### Adding the card

Add it from the dashboard editor (**Add card → Viark Remote Card**), or in YAML:

```yaml
type: custom:viark-remote-card
entity: media_player.viark_sat_4k
```

| Option        | Type    | Default          | Description |
|---------------|---------|------------------|-------------|
| `entity`      | string  | **required**     | The Viark `media_player` or `remote` entity. |
| `name`        | string  | `VIARK`          | Text printed at the bottom of the remote. |
| `show_name`   | boolean | `true`           | Show the name at the bottom. |
| `show_status` | boolean | `true`           | Show power state and current channel in the top window. |
| `haptics`     | boolean | `true`           | Vibrate on press in the companion app. |
| `buttons`     | map     |                  | Per-button overrides, see [below](#button-overrides). |

Either entity type sends the same keys:

| `entity` domain | Keys are sent with     | Power uses            |
|-----------------|------------------------|-----------------------|
| `media_player`  | `viark.send_key`       | `media_player.toggle` |
| `remote`        | `remote.send_command`  | `remote.toggle`       |

When bound to the `remote` entity, the card finds the `media_player` of the same
device to show the channel.

The card is 280 px wide at most. To change that, set `--viark-remote-width`, for
example with [card-mod][card-mod]:

```yaml
card_mod:
  style: |
    :host { --viark-remote-width: 340px; }
```

### Buttons

Each button sends one of the [named keys](#actions), so anything the card does
can also be done from an automation. Power uses the integration's dedicated power
command, so it only wakes the receiver from soft standby. That is a limit of the
receiver.

| Button | Button name | Action |
|---|---|---|
| ⏻ | `power` | toggle power |
| 🔇 | `mute` | `mute` |
| RESOL | `resol` | `resolution` |
| TXT | `txt` | `teletext` |
| AUDIO | `audio` | `audio` |
| SUBT | `subt` | `subtitle` |
| 0 – 9 | `digit_0` … `digit_9` | `digit_0` … `digit_9` |
| < | `chevron_left` | — *not supported yet* |
| > | `chevron_right` | — *not supported yet* |
| VOL + / VOL − | `vol_up` / `vol_down` | `volume_up` / `volume_down` (hold to repeat) |
| CH + / CH − | `ch_up` / `ch_down` | `channel_up` / `channel_down`, the receiver's own channel keys (hold to repeat) |
| FAV | `fav` | `favourite` |
| EPG | `epg` | `epg` |
| INFO | `info` | `info` |
| MENU | `menu` | `menu` |
| RECALL | `recall` | `recall` |
| EXIT | `exit` | `exit` |
| ▲ ▼ ◀ ▶ | `up` `down` `left` `right` | `up` `down` `left` `right` (hold to repeat) |
| OK | `ok` | `ok` |
| Red / Green / Yellow / Blue | `red` `green` `yellow` `blue` | `red` `green` `yellow` `blue` |
| F1 / F2 | `f1` / `f2` | `f1` / `f2` |
| MEDIA | `media` | `usb` |
| UPDATE | `update` | — *not supported yet* |
| ⏪ ▶ ⏸ ⏩ | `rewind` `play` `pause` `fast_forward` | `rewind` `play` `pause` `fast_forward` |
| TIMER | `timer` | `timer` |
| ⏺ / ⏹ | `record` / `stop` | `record` / `stop` |
| TV/R | `tv_radio` | `tv_radio` |

Buttons marked *not supported yet* have no verified key code. Pressing one shows
a short notice and sends nothing. Until a code is confirmed on real hardware (see
[Mapping remote keys](CONTRIBUTING.md#mapping-remote-keys)), use an override.

### Button overrides

The `buttons` option remaps any button by its name from the table above. Each
override needs exactly one of these:

| Field | Effect |
|---|---|
| `key` | Send a different key: a name (`epg`) or a raw key code (`44`). |
| `perform_action` | Run any Home Assistant action. `data` and `target` are optional. |
| `action: none` | Disable the button. |

```yaml
type: custom:viark-remote-card
entity: media_player.viark_sat_4k
name: Living room
buttons:
  # A raw key code the integration has no name for
  chevron_left:
    key: 25
  # Any action
  update:
    perform_action: script.turn_on
    target:
      entity_id: script.receiver_night_mode
  # Tune straight to a channel
  f2:
    perform_action: media_player.select_source
    target:
      entity_id: media_player.viark_sat_4k
    data:
      source: News HD
  # Ignore the button
  timer:
    action: none
```

[`scripts/map_keys_guided.py`](scripts/map_keys_guided.py) steps through the
unverified key codes on a live receiver and helps find the right number for each
button.

### Coming from the separate card

The card used to be its own project, [ha-viark-remote-card][old-card], installed
as a HACS dashboard repository. It ships with the integration from version 1.4.0.
Your cards keep working as they are: the card type (`custom:viark-remote-card`)
and every option are the same.

Remove the old copy, or the dashboard may keep loading it instead of the new one:

1. Update this integration to 1.4.0 or newer and restart Home Assistant.
2. **Installed through HACS:** open HACS, find **Viark Remote Card**, and choose
   **⋮ → Remove**. HACS deletes its dashboard resource too. Then remove
   `https://github.com/jorgediez/ha-viark-remote-card` from **HACS → ⋮ → Custom
   repositories**.
3. **Installed by hand:** delete the `/local/ha-viark-remote-card.js` entry under
   **Settings → Dashboards → ⋮ → Resources**, and the file from `config/www/`.
4. Reload the browser. In the companion app, use **Reset frontend cache**, under
   **Settings → Companion app**, in Debugging on iOS or Troubleshooting on
   Android.

The browser console shows `VIARK-REMOTE-CARD v1.4.0` (or newer) once the new card
is in use.

## Troubleshooting

* **The receiver is not offered during setup.** Discovery listens for the
  receiver's UDP broadcast, which does not reach a Home Assistant container
  without host networking. Enter the IP address by hand.
* **Setup keeps retrying, or the entities are unavailable.** The receiver is
  probably in deep standby, where it leaves the network. Wake it with the
  physical remote; Home Assistant reconnects on its own.
* **"receiver has no free client slot".** The receiver accepts only a few
  clients at once. Close the G-MScreen app on your phones, or any other
  software connected to the receiver, and Home Assistant gets back in on its
  next retry.
* **Changing channel fails with "receiver is showing a menu" or "channel is
  being recorded".** The receiver refuses to tune in those states. Close the
  menu, or wait for the recording.
* **The address changed.** Use **⋮ → Reconfigure** on the integration (see
  [Configuration](#configuration)).
* **The card shows "Configuration error" or "Custom element doesn't exist:
  viark-remote-card".** The card loads once a receiver is set up and Home
  Assistant has restarted with the integration installed. A dashboard opened
  while Home Assistant is still starting misses the card until it is reloaded,
  so reload it once startup has finished. If it persists, clear the browser's
  cache, or the companion app's frontend cache.
* **The remote card behaves like an older version.** An old copy of the separate
  card is still loaded; see
  [Coming from the separate card](#coming-from-the-separate-card). The browser
  console shows `VIARK-REMOTE-CARD vX.Y.Z` when the card loads, and it should
  match the integration's version.
* **The card's buttons are greyed out.** The entity is `unavailable`: the
  integration cannot reach the receiver (see above).
* **The card's arrow keys move a menu instead of changing channel.** That is how
  the receiver behaves while a menu is open on the TV.

When reporting a problem, attach the integration's diagnostics: *Settings →
Devices & Services → Viark → ⋮ → Download diagnostics*. The receiver's address,
serial number and chip ids are redacted, and channel names are left out. A
debug log helps too; enable it from the same menu, or with:

```yaml
logger:
  logs:
    custom_components.viark: debug
```

## Removal

1. Remove the remote card from your dashboards.
2. *Settings → Devices & Services → Viark*, then **⋮ → Delete** on each
   receiver.
3. If you installed through HACS, remove **Viark Satellite Receiver** there;
   otherwise delete `config/custom_components/viark/`.
4. Restart Home Assistant. The card goes with the integration.

Nothing is left on the receiver: it keeps no record of Home Assistant beyond
the open connection.

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

Regenerate with `python scripts/make_brand_images.py` (needs `pillow`), or simply
replace the PNGs. `tests/test_brand_images.py` checks size, squareness,
transparency and filenames.

## Protocol

The receiver speaks an undocumented protocol on TCP 20000. It is described in
full in **[docs/PROTOCOL.md](docs/PROTOCOL.md)** — framing, the obfuscated login
block, reply headers, request numbers, status codes and the remote key table.

That document was assembled by cross-referencing **two independent
reverse-engineering efforts** — one of the GMScreen Android app, one of the
PC-GMScreen Java client — and treating only details they agree on as
established. Everything was then verified against real hardware. Where the two
sources conflict (for example the meaning of notification 2014), the conflict is
recorded and the detail is not relied upon — unless hardware settles it, as
happened with key codes 55 and 63.

## Development

The scripts talk to a receiver directly, without Home Assistant. Set `VIARK_HOST`
or pass `--host`:

```bash
export VIARK_HOST=192.168.1.50

python scripts/viark_cli.py discover              # listen on UDP 25860
python scripts/viark_cli.py info                  # receiver state
python scripts/viark_cli.py now                   # current channel
python scripts/viark_cli.py channels --start 0 --end 20
python scripts/viark_cli.py tune "News HD"           # direct tune by name
python scripts/viark_cli.py key mute
python scripts/viark_cli.py keys                  # key alias table

python scripts/verify_protocol.py                 # re-check protocol claims
python scripts/test_actions.py                    # self-verifying tune + mute
python scripts/map_keys_guided.py --start 24 --end 56 --out keymap.json
python scripts/raw_capture.py --json '{"request":"14"}'
python scripts/ha_import_check.py                 # import against a real HA install
python scripts/make_brand_images.py               # regenerate the brand icons
```

### The remote card

Its source is in `frontend/`, in TypeScript with Lit. The build is committed to
`custom_components/viark/www/viark-remote-card.js`, because HACS installs that
folder from the release's tag and builds nothing.

```bash
cd frontend
npm install
npm run build       # writes custom_components/viark/www/viark-remote-card.js
npm run watch       # rebuild on change
npm run typecheck
npm run lint        # ESLint
npm run format      # Prettier; format:check only reports
npm test
npm run coverage    # tests with a coverage report
npm run demo        # http://localhost:5000, with a mocked Home Assistant
node scripts/check-key-aliases.mjs   # the card's key names match const.py
```

Commit the rebuilt file with every change to the card. CI rebuilds it and fails
when the committed file differs, so a Dependabot update that changes the build
needs a rebuild pushed to its branch.

### Tests

```bash
pip install -r requirements_test.txt
ruff check . && ruff format --check .
pytest
```

The Home Assistant test harness only runs on Linux and macOS. On Windows, use
Docker (`scripts/test-docker.sh`, which runs the same two Home Assistant
versions as CI) or WSL.

No hardware required. The integration is exercised inside Home Assistant against
a mocked receiver: the config flow (discovery, a receiver that moved address,
reconfiguring), setup, retry and unload, diagnostics, and every entity and
action. Below that they cover framing, compact-JSON encoding, XML encoding,
login-block decoding, reply-header layout, status codes, the client's requests,
reconnection against a stub receiver (including concurrent reconnects and write
failures), refresh pacing (the push cooldown, re-reading when the receiver
pushes mid-fetch, and a refused channel lookup), the diagnostic entity
definitions, source-list labelling and channel resolution, and the key table —
including a guard that a single-source code is never presented as verified
unless it has been confirmed on hardware, that `freeze` and `pause` never drift
onto each other's code, and that every entity has both a translated name and an
icon, with no orphans left behind when one is removed.

The card has its own tests in `frontend/`, run with `npm test`: pure logic in
Node, and the card and its editor rendered in happy-dom against a mocked `hass`.

### Releasing

1. Bump the version in `custom_components/viark/manifest.json` and
   `pyproject.toml`, and the card's: `npm version X.Y.Z --no-git-tag-version` in
   `frontend/`, and `VERSION` in `frontend/src/const.ts`. Rebuild the card and
   commit it. Tests check they all match.
2. Publish a GitHub release tagged `vX.Y.Z`. HACS installs from that tag.
3. The **Release** workflow checks the tag matches the version files, then runs
   the tests, the card's checks and hassfest against the tagged code, and the
   HACS validation, which checks the repository through GitHub's API rather than
   the tag. Releases are immutable: if a check fails, fix it and release a new
   version.

## Contributing

Reports from receiver models other than the SAT 4K are the most useful thing
you can send, and some remote key codes still need someone to press them on
real hardware. See [CONTRIBUTING.md](CONTRIBUTING.md) for both, and for how to
work on the code. Questions, and how it does on your receiver, are welcome in
the [Home Assistant community thread][community].

## Disclaimer

This is an unofficial, community project. It is not affiliated with or endorsed
by Viark, the makers of G-MScreen, or any other brand mentioned here. All
trademarks belong to their respective owners. The remote card imitates the
remote's button layout; the name at the bottom is plain text, not the Viark logo.
Use at your own risk.

## Credits

* Two reverse-engineering write-ups of the GMScreen Android app and the
  PC-GMScreen Java client, which supplied the request and key tables.
* [gabonator's ABcom set-top box notes][gabonator] — the original public
  description of the framing and the obfuscated login block.
* [PC-GMScreen][pcgmscreen], which bundles the Java client those notes build on.

## License

[MIT](LICENSE)

[old-card]: https://github.com/jorgediez/ha-viark-remote-card
[card-mod]: https://github.com/thomasloven/lovelace-card-mod
[community]: https://community.home-assistant.io/t/viark-satellite-receivers-and-other-g-mscreen-boxes-local-control-integration/1025250
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/jorgediez/ha-viark
[release-url]: https://github.com/jorgediez/ha-viark/releases
[validate-badge]: https://github.com/jorgediez/ha-viark/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/jorgediez/ha-viark/actions/workflows/validate.yml
[tests-badge]: https://github.com/jorgediez/ha-viark/actions/workflows/tests.yml/badge.svg
[tests-url]: https://github.com/jorgediez/ha-viark/actions/workflows/tests.yml
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[brands]: https://github.com/home-assistant/brands
[my-hacs-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[my-hacs-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=jorgediez&repository=ha-viark&category=integration
[my-setup-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[my-setup-url]: https://my.home-assistant.io/redirect/config_flow_start/?domain=viark
[gabonator]: https://gist.github.com/gabonator/2c8885127cf6e0954c24e5d698ff99b6
[pcgmscreen]: https://github.com/adamlahbib/PC-GMScreen
