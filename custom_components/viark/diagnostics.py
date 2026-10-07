"""Diagnostics for the Viark satellite receiver.

Meant for reports from receiver models other than the one this was built on, so
it carries what tells models apart: the decoded login block, which fields the
state reply has, and how the integration is talking to the receiver.

It leaves out what identifies a user. The address, serial and chip ids are
redacted. Of the state reply, which also carries lock settings, only known fields
are given with their values; the rest are listed by name. Channel names never
appear, since a line-up can say where someone lives.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .coordinator import ViarkConfigEntry

TO_REDACT = {CONF_HOST, "serial", "ip", "cpu_chip_id", "flash_id"}

#: State fields safe to report with their values.
STATE_FIELDS = (
    "ProductName",
    "SoftwareVersion",
    "ChannelNum",
    "MaxNumOfPrograms",
    "PowerMode",
    "MuteState",
)

#: Fields of the tuned channel safe to report; ServiceName is left out.
CHANNEL_FIELDS = ("ServiceIndex", "Radio", "Scramble")


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ViarkConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    client = coordinator.client
    state = coordinator.data
    error = coordinator.last_exception

    diagnostics: dict[str, Any] = {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "login": async_redact_data(client.info, TO_REDACT),
        "connection": {
            "connected": client.connected,
            "data_format": "JSON" if client.use_json else "XML",
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            # str(), not repr(): a translated error's repr is only its key.
            "last_exception": f"{type(error).__name__}: {error}" if error else None,
        },
        "state": None,
    }
    if state is not None:
        current = state.current
        diagnostics["state"] = {
            "values": {k: state.info[k] for k in STATE_FIELDS if k in state.info},
            "fields": sorted(state.info),
            "powered_on": state.powered_on,
            "muted": state.muted,
            "channel_count": state.channel_count,
            "current_channel": None
            if current is None
            else {k: current[k] for k in CHANNEL_FIELDS if k in current},
        }
    return diagnostics
