# Contributing

Thanks for looking. Reports from receivers other than the Viark SAT 4K are the
most useful thing anyone can send: the integration talks to an undocumented
protocol, and receivers on other platforms are known to behave differently.

## Reporting a receiver, or a problem

Open an [issue](https://github.com/jorgediez/ha-viark/issues/new/choose). There
is a form for bugs and one for telling us how the integration does on your
receiver.

What makes a report actionable:

- The integration's diagnostics (*Settings → Devices & Services → Viark → ⋮ →
  Download diagnostics*). The receiver's address, serial number and chip ids are
  redacted, and channel names are left out. They include the platform id, which
  is what tells receiver families apart.
- A debug log covering the moment it went wrong, with
  `custom_components.viark: debug` in your `logger` settings. See
  [Troubleshooting](README.md#troubleshooting).

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

## What belongs here

This integration controls Viark and other G-MScreen receivers over their own LAN
protocol, with nothing in the cloud.

Changes that fit:

- More of what the receiver reports or accepts over the protocol.
- Making an existing feature work on another receiver model.
- Fixing how the integration reacts to what a receiver sends.
- Documentation, especially of receiver behaviour, in docs/PROTOCOL.md.

Changes that belong elsewhere:

- The on-screen remote is [ha-viark-remote-card](https://github.com/jorgediez/ha-viark-remote-card),
  a separate project.
- Enigma2 receivers already have Home Assistant's `enigma2` integration.

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

A pull request is expected to:

- Pass `ruff check`, `ruff format --check` and the test suite. CI runs these
  against the oldest supported Home Assistant and the newest, plus HACS and
  `hassfest`, and needs a maintainer to approve the first run on a fork.
- Come with tests. The integration is tested inside Home Assistant against a
  mocked receiver (`tests/common.py`), and the protocol against a stub receiver
  (`tests/test_reconnect.py`).
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

## License

Contributions are under the [MIT License](LICENSE), like the rest of the project.
