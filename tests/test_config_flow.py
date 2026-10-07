"""Tests for the config flow."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
import voluptuous as vol

from custom_components.viark.const import DOMAIN
from custom_components.viark.protocol import ViarkConnectionError, ViarkRequestError
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    SOURCE_USER,
    ConfigEntryState,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult, FlowResultType

from .common import HOST, PORT, PRODUCT_NAME, SERIAL, make_client


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Keep a created entry from setting up, which these tests do not need."""
    with patch(
        "custom_components.viark.async_setup_entry", return_value=True
    ) as setup_entry:
        yield setup_entry


@pytest.fixture
def mock_discover() -> Generator[AsyncMock]:
    """Hear no receivers broadcasting unless a test says otherwise."""
    with patch(
        "custom_components.viark.config_flow.async_discover", return_value={}
    ) as discover:
        yield discover


@pytest.fixture
def probe_client() -> Generator[MagicMock]:
    """Patch the client the flow uses to check the address."""
    client = make_client()
    with patch("custom_components.viark.config_flow.ViarkClient", return_value=client):
        yield client


def default_host(result: FlowResult) -> str | None:
    """Return the host the form pre-fills, if any."""
    for key in result["data_schema"].schema:
        if key == CONF_HOST and key.default is not vol.UNDEFINED:
            return key.default()
    return None


@pytest.mark.usefixtures("mock_discover")
async def test_user_flow_creates_an_entry(
    hass: HomeAssistant, probe_client: MagicMock, mock_setup_entry: AsyncMock
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == PRODUCT_NAME
    assert result["data"] == {CONF_HOST: HOST, CONF_PORT: PORT}
    assert result["result"].unique_id == SERIAL
    probe_client.disconnect.assert_awaited_once()
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.usefixtures("mock_discover", "mock_setup_entry")
async def test_a_busy_receiver_is_named_after_its_login_block(
    hass: HomeAssistant, probe_client: MagicMock
) -> None:
    """The login block alone identifies the receiver if state is refused."""
    probe_client.state.side_effect = ViarkRequestError(14, 5)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == PRODUCT_NAME  # the model, from the login block


async def test_a_discovered_receiver_is_offered(
    hass: HomeAssistant, mock_discover: AsyncMock
) -> None:
    mock_discover.return_value = {HOST: {}}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert default_host(result) == HOST


async def test_a_configured_receiver_is_not_offered_again(
    hass: HomeAssistant, mock_discover: AsyncMock, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    mock_discover.return_value = {HOST: {}, "192.168.1.51": {}}

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert default_host(result) == "192.168.1.51"


async def test_discovery_failing_still_shows_the_form(
    hass: HomeAssistant, mock_discover: AsyncMock
) -> None:
    """Another process may hold the discovery port; that is not fatal."""
    mock_discover.side_effect = OSError("address in use")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert default_host(result) is None


@pytest.mark.usefixtures("mock_discover", "mock_setup_entry")
async def test_an_unreachable_receiver_shows_an_error_then_recovers(
    hass: HomeAssistant, probe_client: MagicMock
) -> None:
    probe_client.connect.side_effect = ViarkConnectionError("refused")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    probe_client.disconnect.assert_awaited_once()

    probe_client.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.usefixtures("mock_discover", "probe_client")
async def test_a_known_serial_updates_the_address(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """A receiver that moved to a new IP keeps its entry, with the new address."""
    config_entry.add_to_hass(hass)
    new_host = "192.168.1.77"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: new_host, CONF_PORT: PORT}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.data[CONF_HOST] == new_host


@pytest.mark.usefixtures("mock_discover")
async def test_without_a_serial_the_address_identifies_the_receiver(
    hass: HomeAssistant, probe_client: MagicMock
) -> None:
    probe_client.info = {"model": PRODUCT_NAME}
    MockConfigEntry(domain=DOMAIN, data={CONF_HOST: HOST, CONF_PORT: PORT}).add_to_hass(
        hass
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.usefixtures("mock_discover", "probe_client")
async def test_a_moved_receiver_reloads_once(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    """Each reload takes one of the receiver's few client slots; one is enough."""
    new_host = "192.168.1.77"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: new_host, CONF_PORT: PORT}
    )
    await hass.async_block_till_done()

    assert result["reason"] == "already_configured"
    assert init_integration.state is ConfigEntryState.LOADED
    assert mock_client.client_class.call_count == 2
    assert mock_client.client_class.call_args.args[0] == new_host


async def start_reconfigure(hass: HomeAssistant, entry: MockConfigEntry) -> FlowResult:
    """Open the reconfigure form for an entry."""
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )


@pytest.mark.usefixtures("probe_client")
async def test_reconfigure_changes_the_address_and_reloads(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: MagicMock
) -> None:
    new_host = "192.168.1.77"

    result = await start_reconfigure(hass, init_integration)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: new_host, CONF_PORT: PORT}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert init_integration.data == {CONF_HOST: new_host, CONF_PORT: PORT}
    assert init_integration.state is ConfigEntryState.LOADED
    assert mock_client.client_class.call_count == 2
    assert mock_client.client_class.call_args.args[0] == new_host


async def test_reconfigure_retries_an_unreachable_address(
    hass: HomeAssistant, init_integration: MockConfigEntry, probe_client: MagicMock
) -> None:
    probe_client.connect.side_effect = ViarkConnectionError("refused")

    result = await start_reconfigure(hass, init_integration)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.77", CONF_PORT: PORT}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert init_integration.data[CONF_HOST] == HOST


async def test_reconfigure_refuses_a_different_receiver(
    hass: HomeAssistant, init_integration: MockConfigEntry, probe_client: MagicMock
) -> None:
    probe_client.info = {**probe_client.info, "serial": "999999999999"}

    result = await start_reconfigure(hass, init_integration)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.77", CONF_PORT: PORT}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert init_integration.data[CONF_HOST] == HOST


@pytest.mark.usefixtures("mock_client", "probe_client")
async def test_reconfigure_without_a_serial_on_the_entry(hass: HomeAssistant) -> None:
    """An entry made without a serial has nothing to compare, so any receiver goes."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: HOST, CONF_PORT: PORT})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await start_reconfigure(hass, entry)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.77", CONF_PORT: PORT}
    )
    await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == "192.168.1.77"
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
