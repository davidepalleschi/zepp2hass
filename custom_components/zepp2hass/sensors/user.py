"""User Info sensor for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from ..const import DOMAIN, SIGNAL_UPDATE
from .formatters import format_gender, format_birth_date

_LOGGER = logging.getLogger(__name__)


class UserInfoSensor(SensorEntity):
    """Consolidated User Information sensor."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the user info sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} User"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_user_info"
        self._attr_icon = "mdi:account"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            manufacturer="Zepp",
            model="Zepp Smartwatch",
            name=self._device_name,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_native_value is not None

    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE.format(self._entry_id),
                self.async_update_from_payload,
            )
        )

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            user_data = payload.get("user", {})
            if not user_data:
                return
            
            # Set state to nickname
            nickname = user_data.get("nickName", "Unknown User")
            
            # Build attributes dictionary with all user info
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
            
            # Update state and attributes
            if nickname != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                _LOGGER.debug("Updating User Info -> %s with %d attributes", nickname, len(attributes))
                self._attr_native_value = nickname
                self._attr_extra_state_attributes = attributes
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating user info sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor.
        
        Passive sensors, updated only via webhook.
        """
        pass

