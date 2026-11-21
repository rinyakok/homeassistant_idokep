"""Constants for the Idokep Weather integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.util import slugify

DOMAIN = "idokep"
NAME = "Időkép"
ATTRIBUTION = "Data provided by Idokep.hu"
MANUFACTURER = "Időkép"
DEFAULT_LOCATION = "Budapest"

# Version 2: one entry per location, data {"location": ...}. The same layout
# as the FabianGabor/HA-Idokep integration, so its users can switch over.
CONFIG_FLOW_VERSION = 2
CONF_LOCATION = "location"

# Option: length of the daily forecast. 30 days needs one more page
# (/30napos/) per update.
CONF_FORECAST_DAYS = "forecast_days"
DEFAULT_FORECAST_DAYS = 15
FORECAST_DAYS_CHOICES = (15, 30)

# Separate config entry for one map station.
CONF_STATION_CONFIG_ENTRY = "station_config_entry"
CONF_MEASUREMENT_POINT = "measurement_point"
CONF_STATION_NAME = "station_name"
CONF_STATION_UPDATE_INTERVAL = "station_update_interval"
DEFAULT_STATION_UPDATE_INTERVAL = 20
STATION_UPDATE_INTERVAL_CHOICES = tuple(range(5, 61, 5))
CONF_SMOG_SENSORS_ENABLED = "smog_sensors_enabled"
CONF_SMOG_STATIONS = "smog_stations"
CONF_POLLEN_SENSORS_ENABLED = "pollen_sensors_enabled"
CONF_POLLEN_LOCATION = "pollen_location"
CONF_RADAR_CONFIG_ENTRY = "radar_config_entry"
RADAR_CONFIG_ENTRY_TITLE = "Időkép radar"
RADAR_CONFIG_ENTRY_UNIQUE_ID = "idokep-radar"
RADAR_IMAGE_UNIQUE_ID = "radar-latest-image"
RADAR_CAMERA_UNIQUE_ID = "radar-image-stream"

POLLEN_CATEGORIES = {
    "Pázsitfűfélék": "grass",
    "Útifű": "plantain",
    "Csalánfélék": "nettle",
    "Kenderfélék": "hemp",
    "Libatopfélék": "goosefoot",
    "Parlagfű": "ragweed",
    "Üröm": "mugwort",
    "Gombák": "mold",
}

# Version 1 of this integration (before multiple locations).
LEGACY_CONF_LOCATION = "location_name"
LEGACY_UNIQUE_ID = "IdokepWeatherUID"
LEGACY_DEFAULT_TITLE = "IdokepWeather"

ATTR_API_LOCATION = "location"
ATTR_API_NATIVE_TEMPERATURE = "native_temperature"
ATTR_API_NATIVE_TEMPERATURE_UNIT = "native_temperature_unit"
ATTR_API_ALERTS = "alerts"
ATTR_API_HAZARDS = "hazards"
ATTR_API_CONDITION = "condition"
ATTR_API_CONDITION_HU = "condition_hu"
ATTR_API_SHORT_FORECAST = "short_forecast"
ATTR_API_SUNRISE = "sunrise"
ATTR_API_SUNSET = "sunset"
ATTR_API_CURRENT = "current"
ATTR_API_HOURLY_FORECAST = "hourly_forecast"
ATTR_API_DAILY_FORECAST = "daily_forecast"
ATTR_API_STATION_SENSORS = "station_sensors"
ATTR_API_SMOG_SENSORS = "smog_sensors"
ATTR_API_POLLEN_SENSORS = "pollen_sensors"
ATTR_API_POLLEN_LOCATION = "pollen_location"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.WEATHER]
STATION_PLATFORMS = [Platform.SENSOR]
RADAR_PLATFORMS = [Platform.IMAGE, Platform.CAMERA]
BASE_IDOKEP_URL = "https://www.idokep.hu"
USER_AGENT_TEMPLATE = (
    "HomeAssistant-idokep/{integration_version} "
    "HomeAssistant/{ha_version} "
    "(component rinyakok)"
)


def entry_unique_id(location: str) -> str:
    """Return the config entry unique ID for a location ("Érd" -> "erd")."""
    return slugify(location, separator="-")


def weather_unique_id(entry_id: str, location: str) -> str:
    """Return the weather entity unique ID (same format as HA-Idokep)."""
    return f"{entry_id}_weather_{slugify(location)}"


def station_entry_unique_id(station_id: str) -> str:
    """Return a unique config entry ID for one map station."""
    return f"station-{slugify(station_id, separator='-')}"
