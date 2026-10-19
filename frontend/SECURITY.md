# Security policy

## Reporting a vulnerability

Please report it privately, through
[Report a vulnerability](https://github.com/jorgediez/ha-viark-remote-card/security/advisories/new)
on this repository's Security tab. Don't open a public issue or post it in the
community thread. Only the maintainer sees the report, and no email address is
needed.

Describe what you found, how to reproduce it, and which versions of the card,
the integration and Home Assistant you saw it on.

## What counts

- A way to run script in the dashboard through the card, for example from a
  card configuration or from what an entity reports.
- The card sending an action the user didn't configure or press.

Not a vulnerability in the card: a button override runs whatever action its
configuration names. That's the feature, and only someone who can edit the
dashboard can set it. Problems with the receiver or the integration belong in
[the integration's security policy](https://github.com/jorgediez/ha-viark/security/policy).

## Supported versions

Only the latest release gets fixes.

## What to expect

This is a volunteer project. Reports are read and fixed on a best-effort basis,
and you'll hear back in the report itself, where any fix and its release are
coordinated before details are made public.
