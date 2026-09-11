"""Diagnostic sensors for the Viark satellite receiver.

Most of these come from the 108-byte login block the receiver returns to request
998, which carries far more identity than the config entry needs. That block is
read once per connection, so these values only change when the integration
reconnects -- which is the right behaviour for what they describe.

The obscure identifiers are registered disabled by default: they are useful when
reporting a bug against another receiver model, and noise otherwise.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ViarkConfigEntry
from .const import DOMAIN
from .coordinator import ViarkCoordinator


@dataclass(frozen=True, kw_only=True)
class ViarkSensorDescription(SensorEntityDescription):
    """Describes a Viark diagnostic sensor."""

    value_fn: Callable[[dict[str, Any], dict[str, Any]], Any]


def _receiver_clock(state: dict[str, Any]) -> str | None:
    hour, minute = state.get("StbHour"), state.get("StbMin")
    if isinstance(hour, int) and isinstance(minute, int):
        return f"{hour:02d}:{minute:02d}"
    return None


SENSORS: tuple[ViarkSensorDescription, ...] = (
    ViarkSensorDescription(
        key="serial_number",
        translation_key="serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda login, state: state.get("SerialNumber") or login.get("serial"),
    ),
    ViarkSensorDescription(
        key="software_version",
        translation_key="software_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda login, state: state.get("SoftwareVersion"),
    ),
    ViarkSensorDescription(
        key="ip_address",
        translation_key="ip_address",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda login, state: login.get("ip"),
    ),
    ViarkSensorDescription(
        key="platform_id",
        translation_key="platform_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda login, state: login.get("platform_id"),
    ),
    ViarkSensorDescription(
        key="channel_count",
        translation_key="channel_count",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="channels",
        value_fn=lambda login, state: state.get("ChannelNum"),
    ),
    ViarkSensorDescription(
        key="receiver_clock",
        translation_key="receiver_clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda login, state: _receiver_clock(state),
    ),
    # --- registered but disabled by default -------------------------------
    ViarkSensorDescription(
        key="data_format",
        translation_key="data_format",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: "JSON" if login.get("use_json") else "XML",
    ),
    ViarkSensorDescription(
        key="cpu_chip_id",
        translation_key="cpu_chip_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: login.get("cpu_chip_id"),
    ),
    ViarkSensorDescription(
        key="flash_id",
        translation_key="flash_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: login.get("flash_id"),
    ),
    ViarkSensorDescription(
        key="customer_id",
        translation_key="customer_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: login.get("customer_id"),
    ),
    ViarkSensorDescription(
        key="model_id",
        translation_key="model_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: login.get("model_id"),
    ),
    ViarkSensorDescription(
        key="software_version_raw",
        translation_key="software_version_raw",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: login.get("sw_version"),
    ),
    ViarkSensorDescription(
        key="software_sub_version",
        translation_key="software_sub_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: login.get("sw_sub_version"),
    ),
    ViarkSensorDescription(
        key="max_channels",
        translation_key="max_channels",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        native_unit_of_measurement="channels",
        value_fn=lambda login, state: state.get("MaxNumOfPrograms"),
    ),
    ViarkSensorDescription(
        key="satip_mode",
        translation_key="satip_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: login.get("sat2ip"),
    ),
    ViarkSensorDescription(
        key="client_type",
        translation_key="client_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda login, state: login.get("client_type"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ViarkConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Viark diagnostic sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        ViarkSensor(coordinator, entry, description) for description in SENSORS
    )


class ViarkSensor(CoordinatorEntity[ViarkCoordinator], SensorEntity):
    """A read-only value describing the receiver."""

    _attr_has_entity_name = True
    entity_description: ViarkSensorDescription

    def __init__(
        self,
        coordinator: ViarkCoordinator,
        entry: ViarkConfigEntry,
        description: ViarkSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def native_value(self) -> Any:
        state = self.coordinator.data.info if self.coordinator.data else {}
        return self.entity_description.value_fn(self.coordinator.client.info, state)
