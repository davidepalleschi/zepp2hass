"""User Info sensor for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import ZeppDataUpdateCoordinator
from .formatters import format_gender, format_birth_date

_LOGGER = logging.getLogger(__name__)


class UserInfoSensor(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """Consolidated User Information sensor."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the user info sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} User"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_user_info"
        self._attr_icon = "mdi:account"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        
        # Cache device info
        self._cached_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry_id)},
            manufacturer="Zepp",
            model="Zepp Smartwatch",
            name=coordinator.device_name,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._cached_device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self.native_value is not None

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor (nickname)."""
        if not self.coordinator.data:
            return None
        
        user_data = self.coordinator.data.get("user", {})
        if not user_data:
            return None
        
        return user_data.get("nickName", "Unknown User")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        user_data = self.coordinator.data.get("user", {})
        if not user_data:
            return {}
        
        attributes = {}
        
        # Physical characteristics
        if "age" in user_data:
            attributes["age"] = user_data["age"]
        if "height" in user_data:
            attributes["height"] = user_data["height"]
        if "weight" in user_data:
            attributes["weight"] = user_data["weight"]
        if "gender" in user_data:
            attributes["gender"] = format_gender(user_data["gender"])
        
        # Location and region
        if "region" in user_data:
            attributes["region"] = user_data["region"]
        
        # Birth date
        if "birth" in user_data:
            attributes["birth_date"] = format_birth_date(user_data["birth"])
        
        # App information
        if "appVersion" in user_data:
            attributes["app_version"] = user_data["appVersion"]
        if "appPlatform" in user_data:
            attributes["app_platform"] = user_data["appPlatform"]
        
        # Unique identifier
        if "uuid" in user_data:
            attributes["uuid"] = user_data["uuid"]
        
        return attributes
