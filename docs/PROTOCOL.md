# Viark / ALi "G-MScreen" control protocol

This is the protocol the integration implements. It is drawn from **two
independent reverse-engineering efforts** — one of the GMScreen Android app
(`mktvsmart.screen`, decompiled with jadx) and one of the PC-GMScreen Java
client (`G_MScreen.jar`) — cross-referenced with [gabonator's notes][gist], and
then **verified against a live Viark SAT 4K** (platform id 140, JSON mode).

Only details the two sources **agree on** are treated as established. Where they
conflict, or only one documents something, it is called out below and left out of
the integration.

[gist]: https://gist.github.com/gabonator/2c8885127cf6e0954c24e5d698ff99b6

## Transport

| Purpose | Where |
|---|---|
| Discovery (receiver → LAN broadcast) | UDP **25860** |
| Control / data | TCP **20000** |
| Video streaming | RTSP / SAT>IP on TCP **554** |

The receiver must be on or in *soft* standby. In deep standby it leaves the
network and cannot be woken over IP.

## Framing

### Client → receiver

```
b"Start" + b"%07d" % len(body) + b"End" + body
```

Requests are never compressed. The body is JSON or XML, chosen by the receiver
(see the login flags). **JSON must be compact** — `json.dumps` default spacing is
silently rejected. Every JSON value is a string.

### Receiver → client

A 16-byte header, then an optional body:

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 4 | ASCII `GCDH` |
| 4 | 4 | payload length, uint32 **little endian** |
| 8 | 4 | type — the request number answered, or a 2000–2999 notification |
| 12 | 4 | status, 0 = OK |

**`length == 0` means there is no body.** Action requests (`1000`, `1040`, `1041`)
are commonly acknowledged this way. Any body is a zlib stream (`78 9c`).

Replies are matched to requests **by type alone** — there are no sequence ids — so
keep at most one request of a given type outstanding.

## Login (request 998)

Always XML, because the data format is not yet known:

```xml
<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><Command request="998"><data>Home Assistant</data><uuid>…</uuid></Command>
```

The reply is **108 raw bytes with no GCDH header**, obfuscated by reversing the
buffer and XOR-ing each byte with `0x5B` (its own inverse):

```python
plain = bytes(b ^ 0x5B for b in reversed(raw))
```

The same 108 bytes are broadcast on UDP 25860, so discovery yields full identity
without connecting.

| Offset | Size | Field |
|---:|---:|---|
| 0 | 12 | magic `39WwijOog54a` |
| 12 | 8 | serial (`"%06d%06d"` of big-endian 24-bit ints at 0–2 and 3–5) |
| 20 | 32 | model name, NUL-terminated |
| 52 | 8 | CPU chip id |
| 60 | 8 | flash id |
| 68 | 4 | receiver IP — dotted form is `b[71].b[70].b[69].b[68]` |
| 72 | 1 | platform id (Viark SAT 4K = **140**) |
| 73 | 2 | software version, big endian |
| 75 | 1 | customer id |
| 76 | 1 | model id |
| 80 | 4 | software sub-version, little endian |
| 84 | 1 | flags (see below) |

### Flags byte (offset 84)

| Bit | Meaning | Agreement |
|---:|---|---|
| 0 | receiver has no free client slot | both |
| 1 | Android calls it `client_type`; PC calls it "this client is a slave" | **conflicting** |
| 2 | satellite menu supported | both |
| 3–4 | SAT>IP; only PC documents the encoding (1 enabled, 2 disabled) | location only |
| 6 | **data format — 1 JSON, 0 XML** | both |
| 7 | spectrum analyser supported | Android only |

Bits 1 and 3–4 are exposed as raw values by the integration rather than being
coerced into booleans, since a wrong polarity would be worse than a raw number.

Observed on a Viark SAT 4K: `cpu_chip_id` is populated, `flash_id` reads as all
zeros, and bit 0 flips to 1 in the discovery broadcast once a client is
connected — which is the only place it is observable, because a login is
refused while it is set.

> **This matters.** A bare `<Command request="998" />` is enough to get the block,
> but sending the login *without* `<data>` and `<uuid>` left this receiver
> answering `15` and `3` with status 5 (timeout). With a proper login they work.
> An earlier conclusion here that "15 and 3 are unsupported on firmware 1.32" was
> wrong.

## Requests

Agreed by both sources and confirmed working on the hardware:

| # | Purpose | Parameters |
|---:|---|---|
| `0` | channel list | `FromIndex`, `ToIndex` — **max 100 records per page** |
| `3` | playing channel | — → `[{"Data": "<ProgramId>"}]` |
| `15` | receiver info | — → `StbStatus`, `ProductName`, `SoftwareVersion`, `SerialNumber`, `ChannelNum`, `MaxNumOfPrograms` |
| `19` | mute state | — → `[{"Data": "0\|1"}]` |
| `22` | satellite list | — |
| `26` | keepalive | — |
| `998` | login | `data`, `uuid` |
| `1000` | **switch channel** | `array:[{TvState, ProgramId}]` |
| `1009` | stream URL (SAT>IP) | `array:[{TvState, ProgramId}]` |
| `1012` | stop streaming | — |
| `1040` | **remote key** | `array:[{KeyValue}]` |
| `1041` | power / standby | — |

`TvState` is the channel record's `Radio` flag: 0 TV, 1 radio.

**`1009` does not tune the receiver** — it only returns a stream URL for the
mobile app. Tuning is `1000`. (Verified: `1009` left the tuner alone, `1000`
moved it.)

### A firmware-specific extra

Request **`14`** is not consistently documented — the Android source lists `16`
for list flags, the PC source calls `14` "channel list type" — but on firmware
1.32 it returns a *merged* blob covering device info, the receiver clock, mute,
sleep and lock settings in one round trip. The integration prefers it and falls
back to `15`. This is an empirical finding, not an agreed one.

### Notifications (receiver → client, unsolicited)

Agreed by both sources: **2001** playing channel changed · **2002** channel list
changed · **2003** mute changed · **2004** TV/radio switched · **2005** timers
changed · **2015** this client became master · **2019** satellite list changed.

> The sources **conflict on 2014** (Android: lock settings changed; PC: power
> state changed), so its meaning is not relied upon. Any notification simply
> triggers a refresh.

## Status codes

`0` OK · `1` fail · `2` format error · `3` out of memory · `5` timeout ·
`9` wrong password · `16` channel is being recorded · `17` **receiver is showing
a menu**.

Code 17 explains a behaviour that is otherwise baffling: while a menu is open the
receiver refuses to change channel, and injected arrow keys move the menu
selection instead of the channel. A set `Playing` flag is therefore *not* proof
that the box is on live TV.

## Remote key codes (request 1040)

Codes **both sources agree on**, which is what the integration aliases:

| Code | Key | Code | Key | Code | Key |
|---:|---|---:|---|---:|---|
| 1 | Up | 22 | TV/Radio | 43 | USB |
| 2 | Down | 23 | **Mute** | 57 | Info |
| 3 | Left | 29 | Recall | 58 | Record |
| 4 | Right | 30 | Satellite | 59 | Rewind |
| 5 | OK | 31 | Subtitle | 60 | Fast forward |
| 6 | Menu | 32 | EPG | 61 | Play |
| 7 | Exit | 33 | Favourite | 62 | Stop |
| 8–11 | Red/Green/Yellow/Blue | 34 | Teletext | 63 | Pause |
| **12–21** | **Digits 0–9** | 35 / 36 | Volume +/− | 64 | Previous |
| | | 37 / 38 | Page up/down | 65 | Next |
| | | 39 | Find | 42 | **Power** |

Digits are contiguous: 12 is "0", 13 is "1" … 21 is "9".

Confirmed by live round trip: **1** and **2** change channel, **7** closes an
overlay, **23** toggles mute (checked by reading request 19 back), **63** pauses
USB media playback, and **37/38** jump ten rows in the EPG.

### Single-source codes confirmed on the hardware

These appear in only one document, so they began unaliased. Pressing them on a
Viark SAT 4K while watching the TV settled what they do, which outranks a
document that merely omits them. The names below are the labels printed on the
physical remote — twice these were more accurate than the source's own wording.

| Code | Key | Behaviour observed | Source's label |
|---:|---|---|---|
| 24 | Resol | Opens the resolution / refresh-rate menu | "Display" (PC) |
| 26 | Timer | Opens the Event timer menu | "Time" (PC) |
| 44 | F1 | Matches the remote's F1 | F1 (PC) |
| 45 | F2 | Matches the remote's F2 | F2 (PC) |
| 54 | Audio | Opens the audio-language menu | Audio (PC) |
| 55 | — | **Freezes** the picture and stops audio; sending it again resumes, and so does Exit | "Pause" (PC) |
| 69 | CH+ | One channel up on live TV, ten rows in the EPG / channel list | CH + (PC) |
| 70 | CH− | One channel down on live TV, ten rows in the EPG / channel list | CH − (PC) |

Two of those change how the protocol should be read:

**55 and 63 are different keys, and both are real.** The Android app's key table
gives Pause as 63 while its voice-command assets call 55 "pause", which looked
like the sources contradicting each other. They do not: 63 is the remote's Pause
button and acts on USB media playback, whereas 55 freezes live TV and has no
button on the remote at all. It is reachable only over the network.

**69/70 are the receiver's real channel keys**, so the integration aliases
`channel_up`/`channel_down` to them rather than to the arrows. The arrows step the
channel only on live TV — with a menu open they move the selection (see status
17) — so they were always a workaround.

Nothing observable reports a freeze: the receiver keeps answering as though it
were playing, so no entity state is derived from code 55.

**Still not aliased**, documented by a single source and never pressed: 25, 27,
28, 40, 41, 46–53, 56, 66–68, 71–81 (PC only) and 82 Home (Android only). They
can still be sent as raw numbers. Every single-source code tested so far has
matched the PC document's code, which is reason for mild confidence in the rest —
not reason to alias them untested.

Platform-specific tables exist (Android documents a different table for platform
30, PC one for Trident 8471). The Viark is platform 140, so the standard table
applies.

## Keepalive

Both sources agree the receiver drops idle clients, but disagree on the limit
(Android ~60 s, PC 30 s). The client sends request `26` every 10 s, inside both.
