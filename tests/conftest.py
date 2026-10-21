"""Shared fixtures: a mocked receiver client and a loaded config entry."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.viark.const import DOMAIN
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, UrlManager
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .common import HOST, PORT, PRODUCT_NAME, SERIAL, make_client


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None]:
    """Let Home Assistant load the integration from custom_components/."""
    yield


@pytest.fixture(autouse=True)
def frontend(hass: HomeAssistant) -> MagicMock:
    """Stand in for http and frontend, which the integration depends on for the card.

    The real frontend needs the home-assistant-frontend package and a dozen other
    integrations. Marking both as loaded keeps Home Assistant from setting them
    up; the card still goes through the real add_extra_js_url.
    """
    hass.config.components.update({"http", "frontend"})
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()
    hass.data[DATA_EXTRA_MODULE_URL] = UrlManager(lambda *_: None, [])
    return hass.http


@pytest.fixture
def mock_client() -> Generator[MagicMock]:
    """Patch the client the integration creates during setup."""
    client = make_client()
    with patch(
        "custom_components.viark.ViarkClient", return_value=client
    ) as client_class:
        client.client_class = client_class
        yield client


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a config entry for the receiver, as the config flow creates it."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=PRODUCT_NAME,
        unique_id=SERIAL,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_client: MagicMock
) -> AsyncGenerator[MockConfigEntry]:
    """Set up the integration, and unload it afterwards to stop its timers."""
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    yield config_entry
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
