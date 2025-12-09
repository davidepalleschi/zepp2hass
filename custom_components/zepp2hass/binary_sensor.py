"""Binary sensor platform for Zepp2Hass."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZeppDataUpdateCoordinator
from .sensors.formatters import get_nested_value

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zepp2Hass binary sensor platform."""
    entry_id = entry.entry_id
    
    # Get coordinator from stored data
    coordinator: ZeppDataUpdateCoordinator = hass.data[DOMAIN][entry_id]["coordinator"]

    binary_sensors = [
        IsWearingBinarySensor(coordinator),
        IsMovingBinarySensor(coordinator),
        IsSleepingBinarySensor(coordinator),
    ]
    
    async_add_entities(binary_sensors)


class IsWearingBinarySensor(CoordinatorEntity[ZeppDataUpdateCoordinator], BinarySensorEntity):
    """Binary sensor for wearing status (wearing or not wearing)."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the wearing binary sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Is Wearing"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_is_wearing_binary"
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        data = self.coordinator.data
        return data is not None and data.get("is_wearing") is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if wearing."""
        data = self.coordinator.data
        if not data:
            return None
        
        wearing_status = data.get("is_wearing")
        if wearing_status is None:
            return None
        
        # is_wearing values:
        # 0: Not Wearing -> OFF
        # 1: Wearing -> ON
        # 2: In Motion -> ON (still wearing)
        # 3: Not Sure -> OFF (assume not wearing)
        return wearing_status in (1, 2)

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        return "mdi:watch" if self.is_on else "mdi:watch-off"


class IsMovingBinarySensor(CoordinatorEntity[ZeppDataUpdateCoordinator], BinarySensorEntity):
    """Binary sensor for motion status (in motion or not)."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the motion binary sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Is Moving"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_is_moving_binary"
        self._attr_device_class = BinarySensorDeviceClass.MOTION

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        data = self.coordinator.data
        return data is not None and data.get("is_wearing") is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if in motion."""
        data = self.coordinator.data
        if not data:
            return None
        
        wearing_status = data.get("is_wearing")
        if wearing_status is None:
            return None
        
        # is_wearing values:
        # 0: Not Wearing -> OFF
        # 1: Wearing -> OFF
        # 2: In Motion -> ON
        # 3: Not Sure -> OFF
        return wearing_status == 2

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        return "mdi:run" if self.is_on else "mdi:human-handsdown"


class IsSleepingBinarySensor(CoordinatorEntity[ZeppDataUpdateCoordinator], BinarySensorEntity):
    """Binary sensor for sleep status (sleeping or awake)."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the sleeping binary sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Is Sleeping"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_is_sleeping_binary"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        data = self.coordinator.data
        if not data:
            return False
        sleep_status, found = get_nested_value(data, "sleep.status")
        return found and sleep_status is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if sleeping."""
        data = self.coordinator.data
        if not data:
            return None
        
        sleep_status, found = get_nested_value(data, "sleep.status")
        if not found:
            return None
        
        # sleep.status values:
        # 0: Awake -> OFF
        # 1: Sleeping -> ON
        # 2: Not Sure -> OFF
        return sleep_status == 1

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        return "mdi:sleep" if self.is_on else "mdi:sleep-off"
