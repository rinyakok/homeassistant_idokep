"""Support for the Idokep Weather service."""

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
    WeatherEntity,
)
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import WeatherUpdateCoordinator

#from . import OpenweathermapConfigEntry
from .const import (
    ATTR_API_CLOUDS,
    ATTR_API_CONDITION,
    ATTR_API_CURRENT,
    ATTR_API_DAILY_FORECAST,
    ATTR_API_DEW_POINT,
    ATTR_API_NATIVE_TEMPERATURE,
    ATTR_API_NATIVE_TEMPERATURE_UNIT,
    ATTR_API_HOURLY_FORECAST,
    ATTR_API_LOCATION,
    ATTR_API_HUMIDITY,
    ATTR_API_PRESSURE,
    ATTR_API_TEMPERATURE,
    ATTR_API_VISIBILITY_DISTANCE,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_GUST,
    ATTR_API_WIND_SPEED,
    ATTRIBUTION,
    ATTR_FORECAST_NAME,
    DEFAULT_NAME,
    DOMAIN,
    MANUFACTURER,
)
#============================ TO REMOVE ===================================
import logging
_LOGGER = logging.getLogger(__name__)
#============================ TO REMOVE ===================================

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up Idokep weather entity based on a config entry."""
    domain_data = config_entry.runtime_data
    name = domain_data.name
    location = config_entry.data.get(ATTR_API_LOCATION)

    weather_coordinator = domain_data.coordinator

    unique_id = f"{config_entry.unique_id}"
    idokep_weather = IdokepWeather(f"{location}_{ATTR_FORECAST_NAME}", unique_id,weather_coordinator)

    async_add_entities([idokep_weather], False)



class IdokepWeather(SingleCoordinatorWeatherEntity[WeatherUpdateCoordinator]):
    """Implementation of an Idokep Weather sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_should_poll = False

    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_native_visibility_unit = UnitOfLength.METERS

    def __init__( self, name: str, unique_id: str, weather_coordinator: WeatherUpdateCoordinator, ) -> None:
        """Initialize the sensor."""
        super().__init__(weather_coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, unique_id)},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
        )

        self._attr_supported_features = ( WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY )

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        return self.coordinator.data[ATTR_API_CURRENT].get(ATTR_API_CONDITION)

    @property
    def native_temperature(self) -> float | None:
        """Return the temperature."""
        return self.coordinator.data[ATTR_API_CURRENT].get(ATTR_API_NATIVE_TEMPERATURE)
    
    @property
    def native_temperature_unit(self) -> str | None:
        """Return the temperature."""
        return self.coordinator.data[ATTR_API_CURRENT].get(ATTR_API_NATIVE_TEMPERATURE_UNIT)

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return self.coordinator.data[ATTR_API_DAILY_FORECAST]

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        return self.coordinator.data[ATTR_API_HOURLY_FORECAST]