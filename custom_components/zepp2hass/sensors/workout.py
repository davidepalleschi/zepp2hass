"""Workout sensors for Zepp2Hass."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.const import UnitOfTime

from ..const import DOMAIN, SIGNAL_UPDATE
from .formatters import format_sport_type, get_nested_value

_LOGGER = logging.getLogger(__name__)


class WorkoutStatusSensor(SensorEntity):
    """Workout Status sensor with training load as main value and vo2Max/recovery as attributes."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the workout status sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Training Load"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_training_load"
        self._attr_icon = "mdi:dumbbell"
        self._attr_native_unit_of_measurement = "points"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

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
            # Get training load as main value
            training_load, found = get_nested_value(payload, "workout.status.trainingLoad")
            
            if not found:
                return
            
            # Build attributes
            attributes = {}
            
            # VO2 Max
            vo2_max, vo2_found = get_nested_value(payload, "workout.status.vo2Max")
            if vo2_found and vo2_max is not None:
                attributes["vo2_max"] = vo2_max
            
            # Full Recovery Time (in hours)
            recovery_time, recovery_found = get_nested_value(payload, "workout.status.fullRecoveryTime")
            if recovery_found and recovery_time is not None:
                attributes["full_recovery_time_hours"] = recovery_time
            
            # Update if changed
            if training_load != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                _LOGGER.debug("Updating Training Load -> %s (vo2: %s, recovery: %s)", 
                            training_load, attributes.get("vo2_max"), attributes.get("full_recovery_time_hours"))
                self._attr_native_value = training_load
                self._attr_extra_state_attributes = attributes
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating workout status sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor. Passive sensors, updated only via webhook."""
        pass


class WorkoutLastSensor(SensorEntity):
    """Last Workout sensor with detailed attributes."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the last workout sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Last Workout"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_last_workout"
        self._attr_icon = "mdi:run"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

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

    def _format_timestamp(self, timestamp_ms: int) -> datetime | None:
        """Format timestamp from milliseconds to datetime object."""
        try:
            return datetime.fromtimestamp(timestamp_ms)
        except Exception:
            return None

    def _format_duration_minutes(self, duration_ms: int) -> int:
        """Convert duration from milliseconds to minutes."""
        return duration_ms // 60000

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            workout_data = payload.get("workout", {})
            history = workout_data.get("history", [])
            
            if not history:
                return
            
            # Sort history by startTime (most recent first)
            sorted_history = sorted(history, key=lambda x: x.get("startTime", 0), reverse=True)
            last_workout = sorted_history[0] if sorted_history else None
            
            if not last_workout:
                return
            
            # Set state to sport type name
            sport_type_id = last_workout.get("sportType")
            state = format_sport_type(sport_type_id) if sport_type_id else "Unknown"
            
            # Build attributes with all workout details
            attributes = {
                "sport_type_id": sport_type_id,
                "duration_minutes": self._format_duration_minutes(last_workout.get("duration", 0)),
            }
            
            # Add start time as ISO string for better HA compatibility
            start_time = last_workout.get("startTime")
            if start_time:
                dt = self._format_timestamp(start_time)
                if dt:
                    attributes["start_time"] = dt.isoformat()
                    attributes["date"] = dt.strftime("%Y-%m-%d")
                    attributes["time"] = dt.strftime("%H:%M")
            
            # Update if changed
            if state != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                _LOGGER.debug("Updating Last Workout -> %s", state)
                self._attr_native_value = state
                self._attr_extra_state_attributes = attributes
                self.async_write_ha_state()
                
        except Exception as exc:
            _LOGGER.error("Error updating last workout sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor. Passive sensors, updated only via webhook."""
        pass


class WorkoutHistorySensor(SensorEntity):
    """Workout History sensor - shows total count with recent workouts list."""

    def __init__(self, entry_id: str, device_name: str) -> None:
        """Initialize the workout history sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        
        # Set entity attributes
        self._attr_name = f"{device_name} Workout Count"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_workout_history"
        self._attr_icon = "mdi:counter"
        self._attr_native_unit_of_measurement = "workouts"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

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

    def _format_timestamp(self, timestamp_ms: int) -> str:
        """Format timestamp from milliseconds to readable date string."""
        try:
            dt = datetime.fromtimestamp(timestamp_ms)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(timestamp_ms)

    async def async_update_from_payload(self, payload: dict[str, Any]) -> None:
        """Update sensor from webhook payload."""
        try:
            workout_data = payload.get("workout", {})
            history = workout_data.get("history", [])
            
            if not history:
                return
            
            # State is the total count
            total_count = len(history)
            
            # Sort history by startTime (most recent first)
            sorted_history = sorted(history, key=lambda x: x.get("startTime", 0), reverse=True)
            
            # Build simple list for recent workouts (last 10)
            # Format: "2024-01-15 08:30 - Running (45 min)"
            recent_list = []
            for workout in sorted_history[:10]:
                sport_type = workout.get("sportType")
                sport_name = format_sport_type(sport_type) if sport_type else "Unknown"
                start_time = self._format_timestamp(workout.get("startTime", 0))
                duration_min = workout.get("duration", 0) // 60000
                recent_list.append(f"{start_time} - {sport_name} ({duration_min} min)")
            
            # Build attributes
            attributes = {
                "recent_workouts": recent_list,
            }
            
            # Update if changed
            if total_count != self._attr_native_value or attributes != self._attr_extra_state_attributes:
                _LOGGER.debug("Updating Workout Count -> %d", total_count)
                self._attr_native_value = total_count
                self._attr_extra_state_attributes = attributes
                self.async_write_ha_state()
                    
        except Exception as exc:
            _LOGGER.error("Error updating workout history sensor: %s", exc, exc_info=True)

    async def async_update(self) -> None:
        """Update the sensor. Passive sensors, updated only via webhook."""
        pass
