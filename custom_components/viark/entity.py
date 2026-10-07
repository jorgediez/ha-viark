"""Base entity for the Viark satellite receiver."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import ViarkCoordinator


class ViarkEntity(CoordinatorEntity[ViarkCoordinator]):
    """An entity of the one device each receiver is.

    Every entity describes the device in full. Platforms can set up in any order,
    and an entity that only named the device by its identifier could register
    first, before anything had given the device a name.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: ViarkCoordinator, key: str | None) -> None:
        """Initialise from the shared coordinator.

        ``key`` tells the receiver's entities apart. The media player passes None:
        it was the first entity, and its unique id is the bare entry id.
        """
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = entry_id if key is None else f"{entry_id}_{key}"

        login = coordinator.client.info
        info = coordinator.data.info if coordinator.data else {}
        name = info.get("ProductName") or login.get("model") or DEFAULT_NAME
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            manufacturer="Viark",
            model=name,
            name=name,
            sw_version=info.get("SoftwareVersion"),
            serial_number=info.get("SerialNumber") or login.get("serial"),
        )
