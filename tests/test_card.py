"""Tests for serving the remote card that ships with the integration."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.viark.card import CARD_PATH, CARD_URL
from custom_components.viark.const import DOMAIN
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .common import HOST, PORT

MANIFEST = json.loads((CARD_PATH.parents[1] / "manifest.json").read_text("utf-8"))


async def test_the_card_is_served_and_loaded(
    hass: HomeAssistant, frontend: MagicMock
) -> None:
    assert await async_setup_component(hass, DOMAIN, {})

    frontend.async_register_static_paths.assert_awaited_once()
    (config,) = frontend.async_register_static_paths.call_args.args[0]
    assert config.url_path == CARD_URL
    assert config.path == str(CARD_PATH)
    assert config.cache_headers is True
    # The version makes browsers drop a cached card after an update.
    assert hass.data[DATA_EXTRA_MODULE_URL].urls == {
        f"{CARD_URL}?v={MANIFEST['version']}"
    }


async def test_the_card_is_registered_once_for_every_receiver(
    hass: HomeAssistant, frontend: MagicMock, mock_client: MagicMock
) -> None:
    """Registering the same static path twice is an error in Home Assistant."""
    for serial in ("first", "second"):
        entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id=serial,
            data={"host": HOST, "port": PORT},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    frontend.async_register_static_paths.assert_awaited_once()
    assert len(hass.data[DATA_EXTRA_MODULE_URL].urls) == 1

    for entry in hass.config_entries.async_entries(DOMAIN):
        await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


def test_the_built_card_is_committed() -> None:
    """HACS installs custom_components/viark only; the card must be in it."""
    card = CARD_PATH.read_text("utf-8")

    assert '"viark-remote-card"' in card
    # CI checks the build is fresh; this catches a version bump without a rebuild.
    assert f"VIARK-REMOTE-CARD %c v{MANIFEST['version']} " in card
