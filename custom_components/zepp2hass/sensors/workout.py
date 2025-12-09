"""Workout sensors for Zepp2Hass."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import ZeppDataUpdateCoordinator
from .formatters import format_sport_type, get_nested_value

_LOGGER = logging.getLogger(__name__)


class WorkoutStatusSensor(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """Workout Status sensor with training load as main value and vo2Max/recovery as attributes."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the workout status sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Training Load"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_training_load"
        self._attr_icon = "mdi:dumbbell"
        self._attr_native_unit_of_measurement = "points"
        
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
    def native_value(self) -> Any:
        """Return the state of the sensor (training load)."""
        if not self.coordinator.data:
            return None
        
        training_load, found = get_nested_value(self.coordinator.data, "workout.status.trainingLoad")
        return training_load if found else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        attributes = {}
        
        # VO2 Max
        vo2_max, vo2_found = get_nested_value(self.coordinator.data, "workout.status.vo2Max")
        if vo2_found and vo2_max is not None:
            attributes["vo2_max"] = vo2_max
        
        # Full Recovery Time (in hours)
        recovery_time, recovery_found = get_nested_value(self.coordinator.data, "workout.status.fullRecoveryTime")
        if recovery_found and recovery_time is not None:
            attributes["full_recovery_time_hours"] = recovery_time
        
        return attributes


class WorkoutLastSensor(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """Last Workout sensor with detailed attributes."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the last workout sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Last Workout"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_last_workout"
        self._attr_icon = "mdi:run"
        
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

    def _get_sorted_history(self) -> list[dict]:
        """Get sorted workout history (most recent first). Cached per coordinator update."""
        if not self.coordinator.data:
            return []
        
        workout_data = self.coordinator.data.get("workout", {})
        history = workout_data.get("history", [])
        
        if not history:
            return []
        
        # Sort only if needed
        return sorted(history, key=lambda x: x.get("startTime", 0), reverse=True)

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor (sport type name)."""
        sorted_history = self._get_sorted_history()
        if not sorted_history:
            return None
        
        last_workout = sorted_history[0]
        sport_type_id = last_workout.get("sportType")
        return format_sport_type(sport_type_id) if sport_type_id else "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        sorted_history = self._get_sorted_history()
        if not sorted_history:
            return {}
        
        last_workout = sorted_history[0]
        
        attributes = {
            "sport_type_id": last_workout.get("sportType"),
            "duration_minutes": last_workout.get("duration", 0) // 60000,
        }
        
        # Add start time as ISO string
        start_time = last_workout.get("startTime")
        if start_time:
            try:
                dt = datetime.fromtimestamp(start_time)
                attributes["start_time"] = dt.isoformat()
                attributes["date"] = dt.strftime("%Y-%m-%d")
                attributes["time"] = dt.strftime("%H:%M")
            except Exception:
                pass
        
        return attributes


class WorkoutHistorySensor(CoordinatorEntity[ZeppDataUpdateCoordinator], SensorEntity):
    """Workout History sensor - shows total count with recent workouts list."""

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the workout history sensor."""
        super().__init__(coordinator)
        
        # Set entity attributes
        self._attr_name = f"{coordinator.device_name} Workout Count"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.entry_id}_workout_history"
        self._attr_icon = "mdi:counter"
        self._attr_native_unit_of_measurement = "workouts"
        
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
    def native_value(self) -> int | None:
        """Return the state of the sensor (workout count)."""
        if not self.coordinator.data:
            return None
        
        workout_data = self.coordinator.data.get("workout", {})
        history = workout_data.get("history", [])
        
        if not history:
            return None
        
        return len(history)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
        
        workout_data = self.coordinator.data.get("workout", {})
        history = workout_data.get("history", [])
        
        if not history:
            return {}
        
        # Sort and format recent workouts
        sorted_history = sorted(history, key=lambda x: x.get("startTime", 0), reverse=True)
        
        recent_list = []
        for workout in sorted_history[:10]:
            sport_type = workout.get("sportType")
            sport_name = format_sport_type(sport_type) if sport_type else "Unknown"
            
            start_time_ms = workout.get("startTime", 0)
            try:
                dt = datetime.fromtimestamp(start_time_ms)
                start_time = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                start_time = str(start_time_ms)
            
            duration_min = workout.get("duration", 0) // 60000
            recent_list.append(f"{start_time} - {sport_name} ({duration_min} min)")
        
        return {"recent_workouts": recent_list}
