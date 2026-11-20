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

# Optional map station sensors.
CONF_STATION_SENSORS_ENABLED = "station_sensors_enabled"
CONF_MEASUREMENT_POINT = "measurement_point"
DEFAULT_STATION_SENSORS_ENABLED = False

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
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.WEATHER]
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
