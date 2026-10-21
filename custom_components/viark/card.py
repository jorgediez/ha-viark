"""Serve the remote card, which ships with the integration, to the dashboard.

The card's source is in frontend/ at the root of the repository; its build is
committed to www/. Loading it as an extra module puts it on every dashboard,
storage or YAML, without a Lovelace resource to create, update or clean up.
The version in the URL makes browsers fetch the new card after an update.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

CARD_FILENAME: Final = "viark-remote-card.js"
CARD_URL: Final = f"/{DOMAIN}/{CARD_FILENAME}"
CARD_PATH: Final = Path(__file__).parent / "www" / CARD_FILENAME


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card and have the frontend load it."""
    integration = await async_get_integration(hass, DOMAIN)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(CARD_PATH), cache_headers=True)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={integration.version}")
