"""Webhook URL sensor for Zepp2Hass.

Displays the webhook URL as a diagnostic sensor for easy copying.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class WebhookUrlSensor(SensorEntity):
    """Sensor that displays the webhook URL for easy copying.

    This is a diagnostic sensor that shows the full webhook URL
    that should be configured in the Zepp device/app.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:webhook"

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        device_name: str,
        webhook_url: str,
    ) -> None:
        """Initialize the webhook URL sensor.

        Args:
            hass: Home Assistant instance
            entry_id: Config entry ID
            device_name: Name of the device
            webhook_url: Full webhook URL to display
        """
        self._hass = hass
        self._entry_id = entry_id
        self._webhook_url = webhook_url

        self._attr_name = f"{device_name} Webhook URL"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_webhook_url"
        self._attr_native_value = webhook_url

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for entity registry."""
        return DeviceInfo(identifiers={(DOMAIN, self._entry_id)})

    @property
    def available(self) -> bool:
        """Return True - webhook URL is always available."""
        return True

