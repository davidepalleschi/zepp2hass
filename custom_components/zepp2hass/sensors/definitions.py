"""Sensor definitions for Zepp2Hass."""
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfLength,
    UnitOfTime,
)

# Define all sensors you want created per device.
# Each entry: (json_path, sensor_suffix, friendly_name, unit, icon, formatter_function, entity_category, device_class)
# json_path can be a simple key or a dot-separated path for nested values (e.g., "user.age")
# entity_category: None for main sensors, EntityCategory.DIAGNOSTIC for diagnostic info, EntityCategory.CONFIG for config
# device_class: SensorDeviceClass for proper representation in HA
SENSOR_DEFINITIONS = [
    # Record time
    ("record_time", "record_time", "Record Time", None, "mdi:calendar-clock", None, EntityCategory.DIAGNOSTIC, None),

    # Battery - Main sensor
    ("battery.current", "battery", "Battery", PERCENTAGE, "mdi:battery", None, None, SensorDeviceClass.BATTERY),

    # Blood oxygen - Main sensors (commented out - using BloodOxygenSensor instead)
    #("blood_oxygen.current.value", "blood_oxygen", "Blood Oxygen", PERCENTAGE, "mdi:water-percent", None, None, None),
    #("blood_oxygen.current.time", "blood_oxygen_time", "Blood Oxygen Time", None, "mdi:clock-time-four-outline", None, EntityCategory.DIAGNOSTIC, SensorDeviceClass.TIMESTAMP),
    #("blood_oxygen.current.retCode", "blood_oxygen_retcode", "Blood Oxygen Retcode", None, "mdi:alert-circle-outline", None, EntityCategory.DIAGNOSTIC, None),

    # Body temperature - Main sensor
    ("body_temperature.current.value", "body_temperature", "Body Temperature", UnitOfTemperature.CELSIUS, "mdi:thermometer", "format_body_temp", None, SensorDeviceClass.TEMPERATURE),

    # Distance - Main sensor
    ("distance.current", "distance", "Distance", UnitOfLength.METERS, "mdi:map-marker-distance", None, None, SensorDeviceClass.DISTANCE),

    # Heart rate - Main sensors
    ("heart_rate.last", "heart_rate_last", "Heart Rate Last", "bpm", "mdi:heart-pulse", None, None, None),
    ("heart_rate.resting", "heart_rate_resting", "Heart Rate Resting", "bpm", "mdi:heart", None, None, None),
    ("heart_rate.summary.maximum.hr_value", "heart_rate_max", "Heart Rate Max", "bpm", "mdi:heart-flash", None, None, None),

    # Note: PAI is handled by PAISensor (week as main value, day as attribute)
    
    # Sleep - Main sensors
    ("sleep.info.score", "sleep_score", "Sleep Score", "points", "mdi:sleep", None, None, None),
    ("sleep.info.startTime", "sleep_start", "Sleep Start", None, "mdi:clock-start", "format_sleep_time", None, SensorDeviceClass.TIMESTAMP),
    ("sleep.info.endTime", "sleep_end", "Sleep End", None, "mdi:clock-end", "format_sleep_time", None, SensorDeviceClass.TIMESTAMP),
    ("sleep.info.deepTime", "sleep_deep", "Sleep Deep", UnitOfTime.MINUTES, "mdi:weather-night", None, None, SensorDeviceClass.DURATION),
    ("sleep.info.totalTime", "sleep_total", "Sleep Total", UnitOfTime.MINUTES, "mdi:clock-outline", None, None, SensorDeviceClass.DURATION),
    # ("sleep.stg_list.WAKE_STAGE", "sleep_stage_wake", "Sleep Stage Wake", UnitOfTime.MINUTES, "mdi:weather-sunny", None, None, SensorDeviceClass.DURATION),
    # ("sleep.stg_list.REM_STAGE", "sleep_stage_rem", "Sleep Stage Rem", UnitOfTime.MINUTES, "mdi:brain", None, None, SensorDeviceClass.DURATION),
    # ("sleep.stg_list.LIGHT_STAGE", "sleep_stage_light", "Sleep Stage Light", UnitOfTime.MINUTES, "mdi:weather-sunset", None, None, SensorDeviceClass.DURATION),
    # ("sleep.stg_list.DEEP_STAGE", "sleep_stage_deep", "Sleep Stage Deep", UnitOfTime.MINUTES, "mdi:weather-night", None, None, SensorDeviceClass.DURATION),
    # Note: sleep.status is handled by binary_sensor platform (Is Sleeping)


    # Stress - Main sensor
    ("stress.current.value", "stress_value", "Stress Value", "points", "mdi:emoticon-sad-outline", None, None, None),

    # Screen - Diagnostic category
    ("screen.status", "screen_status", "Screen Status", None, "mdi:monitor", None, EntityCategory.DIAGNOSTIC, None),
    ("screen.aod_mode", "screen_aod_mode", "Screen Aod Mode", None, "mdi:monitor-eye", "format_bool", EntityCategory.DIAGNOSTIC, None),
    ("screen.light", "screen_light", "Screen Light", PERCENTAGE, "mdi:brightness-6", None, EntityCategory.DIAGNOSTIC, None),

    # Sport type - Main sensor (workout status is handled by WorkoutStatusSensor)
    # Note: Wearing status is handled by binary_sensor platform
    #("sport.subType", "sport_type", "Sport Type", None, "mdi:run-fast", "format_sport_type", None, None),
]

# Define sensors with target values
# Each entry: (current_path, target_path, sensor_suffix, friendly_name, unit, icon, formatter_function, device_class)
SENSORS_WITH_TARGET = [
    ("calorie.current", "calorie.target", "calories", "Calories", "kcal", "mdi:fire", None, SensorDeviceClass.ENERGY),
    ("fat_burning.current", "fat_burning.target", "fat_burning", "Fat Burning", UnitOfTime.MINUTES, "mdi:run-fast", None, SensorDeviceClass.DURATION),
    ("stands.current", "stands.target", "stands", "Stands", "times", "mdi:human-handsup", None, None),
    ("steps.current", "steps.target", "steps", "Steps", "steps", "mdi:walk", None, None),
]

