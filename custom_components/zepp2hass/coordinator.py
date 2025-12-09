"""DataUpdateCoordinator for Zepp2Hass."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
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
        
        # Shared DeviceInfo for all entities (created once)
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            manufacturer="Zepp",
            model="Zepp Smartwatch",
            name=device_name,
        )
        
        # Cache for computed data (cleared on each update)
        self._sorted_workout_history: list[dict] | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return shared device info for all entities."""
        return self._device_info

    @property
    def sorted_workout_history(self) -> list[dict]:
        """Get sorted workout history (most recent first).
        
        Cached to avoid re-sorting on each property access.
        """
        if self._sorted_workout_history is not None:
            return self._sorted_workout_history
        
        if not self.data:
            return []
        
        workout_data = self.data.get("workout", {})
        history = workout_data.get("history", [])
        
        if not history:
            self._sorted_workout_history = []
            return []
        
        # Sort once and cache
        self._sorted_workout_history = sorted(
            history, 
            key=lambda x: x.get("startTime", 0), 
            reverse=True
        )
        return self._sorted_workout_history

    @property
    def last_workout(self) -> dict | None:
        """Get the most recent workout without sorting the entire list.
        
        Uses max() which is O(n) instead of sort which is O(n log n).
        """
        if not self.data:
            return None
        
        workout_data = self.data.get("workout", {})
        history = workout_data.get("history", [])
        
        if not history:
            return None
        
        # Find max by startTime - more efficient than sorting for single item
        return max(history, key=lambda x: x.get("startTime", 0))

    @callback
    def async_set_updated_data(self, data: dict[str, Any]) -> None:
        """Update data and notify listeners.
        
        This is called from the webhook handler when new data arrives.
        All entities listening to this coordinator will be updated in a single batch.
        """
        # Clear cached computed data when new data arrives
        self._sorted_workout_history = None
        
        # Call parent method which handles notifying all listeners efficiently
        super().async_set_updated_data(data)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data - not used since we receive data via webhook push.
        
        Returns the latest cached data.
        """
        return self.data if self.data else {}
