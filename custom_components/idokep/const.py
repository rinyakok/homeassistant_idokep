"""Consts for the OpenWeatherMap."""

from __future__ import annotations

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_EXCEPTIONAL,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
    ATTR_CONDITION_WINDY_VARIANT,
)
from homeassistant.const import Platform

DOMAIN = "idokep"
DEFAULT_NAME = "IdokepWeather"
DEFAULT_LANGUAGE = "en"
ATTRIBUTION = "Data provided by Idokep.hu"
MANUFACTURER = "Idokep"
DEFAULT_LOCATION = "Budapest"
CONFIG_FLOW_VERSION = 1
ATTR_API_LOCATION = "location_name"
ATTR_API_PRECIPITATION = "precipitation"
ATTR_API_PRECIPITATION_KIND = "precipitation_kind"
ATTR_API_DATETIME = "datetime"
ATTR_API_DEW_POINT = "dew_point"
ATTR_API_WEATHER = "weather"
ATTR_API_TEMPERATURE = "temperature"
ATTR_API_NATIVE_TEMPERATURE = "native_temperature"
ATTR_API_NATIVE_TEMPERATURE_UNIT = "native_temperature_unit"
ATTR_API_WIND_GUST = "wind_gust"
ATTR_API_WIND_SPEED = "wind_speed"
ATTR_API_WIND_BEARING = "wind_bearing"
ATTR_API_HUMIDITY = "humidity"
ATTR_API_PRESSURE = "pressure"
ATTR_API_CONDITION = "condition"
ATTR_API_CLOUDS = "clouds"
ATTR_API_RAIN = "rain"
ATTR_API_SNOW = "snow"
ATTR_API_UV_INDEX = "uv_index"
ATTR_API_VISIBILITY_DISTANCE = "visibility_distance"
ATTR_API_WEATHER_CODE = "weather_code"
ATTR_API_CLOUD_COVERAGE = "cloud_coverage"
ATTR_API_FORECAST = "forecast"
ATTR_API_CURRENT = "current"
ATTR_API_HOURLY_FORECAST = "hourly_forecast"
ATTR_API_DAILY_FORECAST = "daily_forecast"
UPDATE_LISTENER = "update_listener"
PLATFORMS = [Platform.SENSOR, Platform.WEATHER]
BASE_IDOKEP_URL = "https://www.idokep.hu"

