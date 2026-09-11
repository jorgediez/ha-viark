"""Config flow for the Viark satellite receiver."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_PORT, DOMAIN
from .protocol import ViarkClient, ViarkError, async_discover

_LOGGER = logging.getLogger(__name__)

#: Receivers broadcast their identity every few seconds, so a short listen is
#: enough to offer the address instead of asking the user to find it.
DISCOVERY_SECONDS = 4.0


def _schema(default_host: str | None) -> vol.Schema:
    host_field = (
        vol.Required(CONF_HOST, default=default_host)
        if default_host
        else vol.Required(CONF_HOST)
    )
    return vol.Schema(
        {
            host_field: cv.string,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        }
    )


async def _async_probe(host: str, port: int) -> dict[str, Any]:
    """Connect and read identity, so setup fails fast on a wrong address.

    The login block alone identifies the receiver, so this succeeds even if the
    box is busy enough to refuse follow-up queries.
    """
    client = ViarkClient(host, port, client_name="Home Assistant")
    try:
        await client.connect()
        identity = dict(client.info)
        try:
            state = await client.state()
        except ViarkError:
            state = {}
        identity["product_name"] = state.get("ProductName") or identity.get("model")
        return identity
    finally:
        await client.disconnect()


class ViarkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Viark."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            try:
                info = await _async_probe(host, port)
            except ViarkError as exc:
                _LOGGER.debug("Viark probe of %s:%s failed: %s", host, port, exc)
                errors["base"] = "cannot_connect"
            else:
                serial = info.get("serial")
                if serial:
                    await self.async_set_unique_id(str(serial))
                    self._abort_if_unique_id_configured(
                        updates={CONF_HOST: host, CONF_PORT: port}
                    )
                else:
                    self._async_abort_entries_match({CONF_HOST: host})

                return self.async_create_entry(
                    title=info.get("product_name") or f"Viark {host}",
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(await self._async_discovered_host()),
            errors=errors,
        )

    async def _async_discovered_host(self) -> str | None:
        """Offer a receiver heard broadcasting on the LAN, if there is one."""
        try:
            found = await async_discover(DISCOVERY_SECONDS)
        except OSError as exc:
            # Another process may already hold the discovery port; not fatal.
            _LOGGER.debug("Viark discovery unavailable: %s", exc)
            return None

        configured = {entry.data.get(CONF_HOST) for entry in self._async_current_entries()}
        for host in found:
            if host not in configured:
                return host
        return None
