# Viark Remote Card

[![hacs][hacs-badge]][hacs-url]
[![release][release-badge]][release-url]
[![validate][validate-badge]][validate-url]
[![license][license-badge]](LICENSE)

A Home Assistant dashboard card that looks and works like the remote control of a
**Viark** satellite receiver. Every button of the physical remote is on the card,
in the same place.

It is the companion card for the
**[Viark Satellite Receiver integration][integration]** and sends keys through the
actions that integration provides.

<p align="center">
  <img src="https://raw.githubusercontent.com/jorgediez/ha-viark-remote-card/main/images/screenshot.png" alt="Viark Remote Card" width="320">
</p>

## Features

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

## Requirements

- Home Assistant 2024.6 or newer.
- The [Viark Satellite Receiver integration][integration] **1.1.0 or newer**, set up
  and working. Older versions lack the RESOL, AUDIO, TIMER, F1 and F2 keys, and
  send CH+/CH− as the up/down arrows. Version **1.2.0** is recommended: it fixes
  reconnection after a network drop or a receiver reboot.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository in HACS.][my-badge]][my-url]

Or manually in HACS:

1. Open **HACS**, then ⋮ → **Custom repositories**.
2. Add `https://github.com/jorgediez/ha-viark-remote-card` with type **Dashboard**.
3. Search for **Viark Remote Card**, download it, and reload the browser.

HACS registers the dashboard resource for you.

### Manual

1. Download `ha-viark-remote-card.js` from the [latest release][release-url].
2. Copy it to `config/www/ha-viark-remote-card.js`.
3. Go to **Settings → Dashboards → ⋮ → Resources**, add
   `/local/ha-viark-remote-card.js` as a **JavaScript module**, and reload the browser.

## Configuration

Add the card from the dashboard editor (**Add card → Viark Remote Card**), or in YAML:

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

## Buttons

Each button sends one of the named keys in the integration's key table. Power
uses the integration's dedicated power command, so it only wakes the receiver from
soft standby. That is a limit of the receiver.

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

Buttons marked *not supported yet* have no verified key code in the integration.
Pressing one shows a short notice and sends nothing. Once a code is confirmed on
real hardware, add it to the integration's `KEY_ALIASES` and to this card's button
table. Until then, use an override.

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

The integration repository includes `tools/map_keys_guided.py`, which steps
through the unverified key codes on a live receiver and helps find the right
number for each button.

## Troubleshooting

- **"Custom element doesn't exist: viark-remote-card"**: the resource is not
  loaded. Check **Settings → Dashboards → Resources**, then clear the browser or
  companion app cache.
- **"Unknown Viark key 'resolution'"** (or `audio`, `timer`, `f1`, `f2`): the
  integration is older than 1.1.0. Update it.
- **"Receiver has no free client slot"**: the receiver accepts only a few clients
  at once. Close the G-MScreen phone app if it is connected. If it happens after a
  network drop or a receiver reboot, update the integration to 1.2.0, which fixes
  a stale connection holding a slot.
- **Buttons are greyed out**: the entity is `unavailable`. The integration cannot
  reach the receiver. In deep standby it leaves the network and cannot be woken
  over IP.
- **Arrow keys move a menu instead of changing channel**: that is how the receiver
  behaves while a menu is open on the TV.
- The browser console shows `VIARK-REMOTE-CARD vX.Y.Z` when the card loads,
  which tells you which version is installed.

## Development

```bash
npm install
npm run build       # dist/ha-viark-remote-card.js
npm run watch       # rebuild on change
npm run typecheck
npm test
npm run demo        # http://localhost:5000, with a mocked Home Assistant
```

To try it in Home Assistant, copy `dist/ha-viark-remote-card.js` to `config/www/` and
add it as a resource, as in [manual installation](#manual).

### Releasing

1. Bump `version` in `package.json` and `VERSION` in `src/const.ts`. A test
   checks they match.
2. Publish a GitHub release tagged `vX.Y.Z`.
3. The **Release** workflow builds the card and attaches `ha-viark-remote-card.js`,
   which is the file HACS installs.

## Trademark

This is a community project, not affiliated with or endorsed by Viark. The card
imitates the remote's button layout. The name at the bottom is plain text, not the
Viark logo.

## License

[MIT](LICENSE)

[integration]: https://github.com/jorgediez/ha-viark
[card-mod]: https://github.com/thomasloven/lovelace-card-mod
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/jorgediez/ha-viark-remote-card
[release-url]: https://github.com/jorgediez/ha-viark-remote-card/releases/latest
[validate-badge]: https://github.com/jorgediez/ha-viark-remote-card/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/jorgediez/ha-viark-remote-card/actions/workflows/validate.yml
[license-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[my-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[my-url]: https://my.home-assistant.io/redirect/hacs_repository/?owner=jorgediez&repository=ha-viark-remote-card&category=plugin
