"""Diagnostic binary sensors for the Viark satellite receiver.

These read the capability and status flags packed into byte 84 of the login
block. Only the flag bits both reverse-engineering sources agree on are exposed
here; the ambiguous ones are surfaced as raw values by the sensor platform
instead of being given a possibly-wrong true/false meaning.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ViarkConfigEntry
from .const import DOMAIN
from .coordinator import ViarkCoordinator


@dataclass(frozen=True, kw_only=True)
class ViarkBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Viark diagnostic binary sensor."""

    value_fn: Callable[[dict[str, Any]], bool | None]


# Note: the login block's "receiver full" bit is deliberately NOT exposed here.
# The client refuses to complete a login when it is set, so for any connected
# client it is always false -- an entity for it could never report a problem.
# It is only meaningful in the UDP discovery broadcast, before connecting.
BINARY_SENSORS: tuple[ViarkBinarySensorDescription, ...] = (
    ViarkBinarySensorDescription(
        key="satellite_menu",
        translation_key="satellite_menu",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda login: login.get("sat_enable"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ViarkConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Viark diagnostic binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        ViarkBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class ViarkBinarySensor(CoordinatorEntity[ViarkCoordinator], BinarySensorEntity):
    """A capability or status flag from the receiver's login block."""

    _attr_has_entity_name = True
    entity_description: ViarkBinarySensorDescription

    def __init__(
        self,
        coordinator: ViarkCoordinator,
        entry: ViarkConfigEntry,
        description: ViarkBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.client.info)
