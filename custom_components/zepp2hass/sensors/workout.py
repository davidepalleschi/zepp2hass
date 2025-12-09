"""Workout sensors for Zepp2Hass.

Provides sensors for workout tracking:
- WorkoutStatusSensor: Training load and VO2 max
- WorkoutLastSensor: Most recent workout details
- WorkoutHistorySensor: Workout count and recent history
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .base import ZeppSensorBase
from .formatters import (
    format_sport_type,
    format_timestamp_parts,
    format_duration_minutes,
)

if TYPE_CHECKING:
    from ..coordinator import ZeppDataUpdateCoordinator


class WorkoutStatusSensor(ZeppSensorBase):
    """Workout Status sensor with training load as main value.

    Exposes VO2 max and recovery time as attributes.
    """

    _TRAINING_LOAD_PATH = "workout.status.trainingLoad"
    _VO2_MAX_PATH = "workout.status.vo2Max"
    _RECOVERY_TIME_PATH = "workout.status.fullRecoveryTime"

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the workout status sensor."""
        super().__init__(
            coordinator=coordinator,
            key="training_load",
            name="Training Load",
            icon="mdi:dumbbell",
            unit="points",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self._is_coordinator_ready():
            return False
        _, found = self._get_value(self._TRAINING_LOAD_PATH)
        return found

    @property
    def native_value(self) -> Any:
        """Return the training load value."""
        training_load, found = self._get_value(self._TRAINING_LOAD_PATH)
        return training_load if found else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes (VO2 max, recovery time)."""
        if not self._data:
            return {}

        attributes: dict[str, Any] = {}

        # VO2 Max
        vo2_max, vo2_found = self._get_value(self._VO2_MAX_PATH)
        if vo2_found and vo2_max is not None:
            attributes["vo2_max"] = vo2_max

        # Full Recovery Time (in hours)
        recovery_time, recovery_found = self._get_value(self._RECOVERY_TIME_PATH)
        if recovery_found and recovery_time is not None:
            attributes["full_recovery_time_hours"] = recovery_time

        return attributes


class WorkoutLastSensor(ZeppSensorBase):
    """Last Workout sensor showing most recent workout type and details.

    Main value is the sport type name.
    Attributes include start time, date, duration.
    """

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the last workout sensor."""
        super().__init__(
            coordinator=coordinator,
            key="last_workout",
            name="Last Workout",
            icon="mdi:run",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._is_coordinator_ready() and self.coordinator.last_workout is not None

    @property
    def native_value(self) -> str | None:
        """Return the sport type name of the last workout."""
        last_workout = self.coordinator.last_workout
        if not last_workout:
            return None

        sport_type_id = last_workout.get("sportType")
        return format_sport_type(sport_type_id) if sport_type_id else "Unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes (time, date, duration)."""
        last_workout = self.coordinator.last_workout
        if not last_workout:
            return {}

        attributes: dict[str, Any] = {
            "sport_type_id": last_workout.get("sportType"),
            "duration_minutes": format_duration_minutes(last_workout.get("duration")),
        }

        # Add formatted time attributes
        time_parts = format_timestamp_parts(last_workout.get("startTime"))
        if time_parts:
            attributes["start_time"] = time_parts["iso"]
            attributes["date"] = time_parts["date"]
            attributes["time"] = time_parts["time"]

        return attributes


class WorkoutHistorySensor(ZeppSensorBase):
    """Workout History sensor showing total count with recent workouts list.

    Main value is the total workout count.
    Attributes include a list of recent workouts (max 10).
    """

    _MAX_RECENT_WORKOUTS = 10
    _SECTION = "workout"

    def __init__(self, coordinator: ZeppDataUpdateCoordinator) -> None:
        """Initialize the workout history sensor."""
        super().__init__(
            coordinator=coordinator,
            key="workout_history",
            name="Workout Count",
            icon="mdi:counter",
            unit="workouts",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self._is_coordinator_ready():
            return False
        workout_data = self._get_section(self._SECTION)
        return bool(workout_data.get("history"))

    @property
    def native_value(self) -> int | None:
        """Return the total workout count."""
        workout_data = self._get_section(self._SECTION)
        history = workout_data.get("history", [])
        return len(history) if history else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes (recent workouts list)."""
        sorted_history = self.coordinator.sorted_workout_history
        if not sorted_history:
            return {}

        recent_list = [
            self._format_workout_summary(workout)
            for workout in sorted_history[: self._MAX_RECENT_WORKOUTS]
        ]
        return {"recent_workouts": recent_list}

    @staticmethod
    def _format_workout_summary(workout: dict[str, Any]) -> str:
        """Format a single workout entry as a summary string.

        Format: "YYYY-MM-DD HH:MM - Sport Name (XX min)"
        """
        # Format sport type
        sport_type = workout.get("sportType")
        sport_name = format_sport_type(sport_type) if sport_type else "Unknown"

        # Format start time
        time_parts = format_timestamp_parts(workout.get("startTime"))
        start_time = time_parts.get("date", "Unknown")
        if "time" in time_parts:
            start_time = f"{start_time} {time_parts['time']}"

        # Format duration
        duration_min = format_duration_minutes(workout.get("duration")) or 0

        return f"{start_time} - {sport_name} ({duration_min} min)"
