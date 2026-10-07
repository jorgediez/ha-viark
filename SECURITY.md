# Security policy

## Reporting a vulnerability

Please report it privately, through
[Report a vulnerability](https://github.com/jorgediez/ha-viark/security/advisories/new)
on this repository's Security tab. Don't open a public issue or post it in the
community thread. Only the maintainer sees the report, and no email address is
needed.

Describe what you found, how to reproduce it, and which versions of the
integration and Home Assistant you saw it on.

## What counts

- Diagnostics that contain what they are meant to leave out: the receiver's
  address, serial number or chip ids, or channel names.
- Anything that lets someone control the receiver through Home Assistant beyond
  what the integration's entities and actions offer.
- A way to make the integration run code, or crash Home Assistant, from what a
  receiver sends.

Not a vulnerability in this integration: the receiver's own protocol has no
authentication, so anything on the same network can control the box directly,
with or without Home Assistant. That's how these receivers work, and nothing the
integration does can change it. Keep the receiver on a network you trust.

## Supported versions

Only the latest release gets fixes.

## What to expect

This is a volunteer project. Reports are read and fixed on a best-effort basis,
and you'll hear back in the report itself, where any fix and its release are
coordinated before details are made public.
