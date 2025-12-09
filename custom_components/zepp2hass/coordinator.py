"""DataUpdateCoordinator for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ZeppDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage Zepp data updates from webhook.
    
    This coordinator receives data pushed from webhook and notifies all entities
    in a single batched update, avoiding the overhead of individual dispatcher signals.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str, device_name: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            # No polling - data is pushed via webhook
            update_interval=None,
        )
        self.entry_id = entry_id
        self.device_name = device_name
        # Store the latest payload
        self._latest_data: dict[str, Any] = {}

    @property
    def latest_data(self) -> dict[str, Any]:
        """Return the latest data received."""
        return self._latest_data

    @callback
    def async_set_updated_data(self, data: dict[str, Any]) -> None:
        """Update data and notify listeners.
        
        This is called from the webhook handler when new data arrives.
        All entities listening to this coordinator will be updated in a single batch.
        """
        self._latest_data = data
        # Call parent method which handles notifying all listeners efficiently
        super().async_set_updated_data(data)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data - not used since we receive data via webhook push.
        
        Returns the latest cached data.
        """
        return self._latest_data

