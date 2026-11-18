"""Constants for the Idokep Weather integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "idokep"
DEFAULT_NAME = "IdokepWeather"
ATTRIBUTION = "Data provided by Idokep.hu"
MANUFACTURER = "Idokep"
DEFAULT_LOCATION = "Budapest"
CONFIG_FLOW_VERSION = 1
ATTR_API_LOCATION = "location_name"
ATTR_API_NATIVE_TEMPERATURE = "native_temperature"
ATTR_API_NATIVE_TEMPERATURE_UNIT = "native_temperature_unit"
ATTR_API_CONDITION = "condition"
ATTR_API_CURRENT = "current"
ATTR_API_HOURLY_FORECAST = "hourly_forecast"
ATTR_API_DAILY_FORECAST = "daily_forecast"
ATTR_UID = "IdokepWeatherUID"
ATTR_FORECAST_NAME = "Forecast"
PLATFORMS = [Platform.SENSOR, Platform.WEATHER]
BASE_IDOKEP_URL = "https://www.idokep.hu"
USER_AGENT_TEMPLATE = (
    "HomeAssistant-idokep/{integration_version} "
    "HomeAssistant/{ha_version} "
    "(component rinyakok)"
)
