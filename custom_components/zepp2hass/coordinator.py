"""DataUpdateCoordinator for Zepp2Hass.

This module provides the central data coordinator that:
- Receives data pushed from webhooks (no polling)
- Notifies all entities via batched updates
- Caches computed data like sorted workout history
- Provides shared device info for all entities
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, DEFAULT_MANUFACTURER, DEFAULT_MODEL

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class ZeppDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Zepp data updates via webhook.

    Unlike typical coordinators that poll for data, this one receives
    data pushed from webhooks. It provides:
    - Shared device info for all entities (created once)
    - Cached computed data (e.g., sorted workout history)
    - Efficient batched updates to all listening entities

    Attributes:
        entry_id: Config entry ID for this device
        device_name: Human-readable device name
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        device_name: str,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            config_entry: Config entry for this device
            device_name: Human-readable device name
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.entry_id}",
            config_entry=config_entry,  # Link to config entry (best practice)
            update_interval=None,  # No polling - data pushed via webhook
            always_update=False,  # Only notify listeners if data actually changed
        )
        self.entry_id = config_entry.entry_id
        self.device_name = device_name

        # Shared DeviceInfo (created once, used by all entities)
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, self.entry_id)},
            manufacturer=DEFAULT_MANUFACTURER,
            model=DEFAULT_MODEL,
            name=device_name,
        )

        # Cached computed data (invalidated on each update)
        self._sorted_workout_history: list[dict[str, Any]] | None = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return shared device info for all entities.

        All sensors use this to link to the same device in HA.
        """
        return self._device_info

    @property
    def sorted_workout_history(self) -> list[dict[str, Any]]:
        """Get workout history sorted by start time (most recent first).

        Results are cached until new data arrives via async_set_updated_data.

        Returns:
            List of workout dicts sorted by startTime descending
        """
        if self._sorted_workout_history is not None:
            return self._sorted_workout_history

        if not self.data:
            return []

        history = self.data.get("workout", {}).get("history", [])
        if not history:
            self._sorted_workout_history = []
            return []

        self._sorted_workout_history = sorted(
            history,
            key=lambda x: x.get("startTime", 0),
            reverse=True,
        )
        return self._sorted_workout_history

    @property
    def last_workout(self) -> dict[str, Any] | None:
        """Get the most recent workout.

        Uses max() for O(n) efficiency instead of sorting O(n log n).

        Returns:
            Most recent workout dict or None if no workouts
        """
        if not self.data:
            return None

        history = self.data.get("workout", {}).get("history", [])
        if not history:
            return None

        return max(history, key=lambda x: x.get("startTime", 0))

    @callback
    def async_set_updated_data(self, data: dict[str, Any]) -> None:
        """Update data and notify all listening entities.

        Called from webhook handler when new data arrives.
        Invalidates cached computed data before notifying listeners.

        Args:
            data: New data payload from webhook
        """
        # Invalidate cached computed data
        self._sorted_workout_history = None

        # Delegate to parent to store data and notify listeners
        super().async_set_updated_data(data)

    async def _async_update_data(self) -> dict[str, Any]:
        """Return cached data (no polling - data pushed via webhook).

        This method is required by DataUpdateCoordinator but we don't
        use it for active polling since data arrives via webhooks.

        Returns:
            Current cached data or empty dict
        """
        return self.data if self.data else {}
