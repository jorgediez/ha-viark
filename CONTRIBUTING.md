# Contributing

Thanks for looking. Reports from receivers other than the Viark SAT 4K are the
most useful thing anyone can send: the integration talks to an undocumented
protocol, and receivers on other platforms are known to behave differently.

## Reporting a receiver, or a problem

The [community thread](https://community.home-assistant.io/t/viark-satellite-receivers-and-other-g-mscreen-boxes-local-control-integration/1025250)
is the easiest place for questions, and for "it works on my receiver" or "it
behaves oddly". Bugs are better as an
[issue](https://github.com/jorgediez/ha-viark/issues/new/choose), where there is
a form for bugs, one for the remote card, and one for telling us how the
integration does on your receiver.

Problems with the remote card itself (layout, buttons, the editor, a button that
sends the wrong key) go in a **Card bug report**, with your card YAML and the
browser or companion app. If the receiver doesn't react, a key is unknown, or
the connection fails, that is the integration's side: use the **Bug report**
form. Questions about the card have their own
[community thread](https://community.home-assistant.io/t/custom-card-viark-remote-card-the-receivers-remote-on-your-dashboard/1025251).

What makes a report actionable:

- The integration's diagnostics (*Settings → Devices & Services → Viark → ⋮ →
  Download diagnostics*). The receiver's address, serial number and chip ids are
  redacted, and channel names are left out. They include the platform id, which
  is what tells receiver families apart.
- A debug log covering the moment it went wrong, with
  `custom_components.viark: debug` in your `logger` settings. See
  [Troubleshooting](README.md#troubleshooting).

A security problem should not go in an issue or the thread: see
[SECURITY.md](SECURITY.md) for how to report it privately.

## Mapping remote keys

Key codes 25, 27, 28, 40, 41, 46–53, 56, 66–68 and 71–82 appear in only one of
the two reverse-engineering sources and have not been pressed on real hardware,
so they are deliberately not aliased. If you map any of them,
`scripts/map_keys_guided.py` steps through codes and records what each did. A pull
request adding them to `KEY_ALIASES` is welcome.

Name them after the label on your remote rather than the one in
[docs/PROTOCOL.md](docs/PROTOCOL.md): where the two have differed, the remote was
right. Eight codes have already made that trip (24, 26, 44, 45, 54, 55, 69, 70)
and are recorded in docs/PROTOCOL.md with the behaviour observed.

The remote card sends keys by name, so a new name usually means a card change in
the same pull request:

1. Update `frontend/tests/integration-key-aliases.json`.
   `node frontend/scripts/check-key-aliases.mjs` says what changed, and CI runs
   it on every pull request.
2. Point the button at the new name in `frontend/src/buttons.ts`. If it was one
   of the unsupported buttons, update the list in `frontend/src/localize.ts` and
   the test that counts them.
3. Update the button table in the README, and rebuild the card.

## What belongs here

This integration controls Viark and other G-MScreen receivers over their own LAN
protocol, with nothing in the cloud.

Changes that fit:

- More of what the receiver reports or accepts over the protocol.
- Making an existing feature work on another receiver model.
- Fixing how the integration reacts to what a receiver sends.
- Documentation, especially of receiver behaviour, in docs/PROTOCOL.md.
- Making the remote card behave or look more like the physical remote, and its
  accessibility, translations and visual editor.

Changes that belong elsewhere:

- Enigma2 receivers already have Home Assistant's `enigma2` integration.
- Remotes of other receivers: a separate card, so this one can stay a faithful
  replica.

**If a change is more than a small fix, open an issue first.** A short
description of what you want and how you'd do it takes minutes and can save you
days.

## Working on the code

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/pytest --cov
```

The Home Assistant test harness only runs on Linux and macOS. On Windows, use
WSL. The scripts in `scripts/` talk to a receiver directly, without Home
Assistant; the [README](README.md#development) lists them.

The remote card is in `frontend/`, and needs Node 24:

```bash
cd frontend
npm install
npm run lint && npm run format:check && npm run typecheck
npm test
npm run build       # then commit custom_components/viark/www/viark-remote-card.js
npm run demo        # the card in a browser, with a mocked Home Assistant
```

A pull request is expected to:

- Pass `ruff check`, `ruff format --check` and the test suite. CI runs these
  against the oldest supported Home Assistant and the newest, plus HACS and
  `hassfest`, and needs a maintainer to approve the first run on a fork.
- For the card, pass lint, the format check, the type check and its tests, and
  include the rebuilt `www/viark-remote-card.js`. CI fails if it doesn't match a
  fresh build.
- Come with tests. The integration is tested inside Home Assistant against a
  mocked receiver (`tests/common.py`), and the protocol against a stub receiver
  (`tests/test_reconnect.py`). The card's logic is tested in Node
  (`frontend/tests/actions.test.ts`); the card and its editor render in happy-dom
  against a mocked `hass` (`frontend/tests/card.test.ts`,
  `frontend/tests/editor.test.ts`).
- Update the docs it affects: the README for what users see, docs/PROTOCOL.md for
  what was learned about the protocol.
- Explain, in the commit message, why the change is the way it is — particularly
  anything that works around how a receiver behaves.

Keep a pull request to one subject. Two unrelated improvements are two pull
requests, and they'll both move faster.

## Style

Follow [Home Assistant's own conventions](https://developers.home-assistant.io/docs/development_guidelines)
and the code already here: entity names and errors translated, no blocking calls
in the event loop, comments that say why rather than what.

In the card, Prettier (line length 88) and ESLint decide formatting, and
user-facing text goes through `localize`, in English and Spanish.

## License

Contributions are under the [MIT License](LICENSE), like the rest of the project.
