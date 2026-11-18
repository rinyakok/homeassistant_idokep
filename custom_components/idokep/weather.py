"""Weather entity for the Idokep Weather service."""

from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import IdokepConfigEntry
from .const import (
    ATTR_API_CONDITION,
    ATTR_API_CURRENT,
    ATTR_API_DAILY_FORECAST,
    ATTR_API_HOURLY_FORECAST,
    ATTR_API_NATIVE_TEMPERATURE,
    ATTRIBUTION,
    CONF_LOCATION,
    weather_unique_id,
)
from .coordinator import WeatherUpdateCoordinator
from .entity import idokep_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the weather entity of one location."""
    async_add_entities([IdokepWeather(entry.runtime_data.coordinator)])


class IdokepWeather(SingleCoordinatorWeatherEntity[WeatherUpdateCoordinator]):
    """The Időkép weather entity of one location."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    # The entity uses the device name ("Időkép Érd"): weather.idokep_erd
    _attr_name = None

    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator: WeatherUpdateCoordinator) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = weather_unique_id(
            entry.entry_id, entry.data[CONF_LOCATION]
        )
        self._attr_device_info = idokep_device_info(entry)

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        return self.coordinator.data[ATTR_API_CURRENT][ATTR_API_CONDITION]

    @property
    def native_temperature(self) -> float | None:
        """Return the temperature."""
        return self.coordinator.data[ATTR_API_CURRENT][ATTR_API_NATIVE_TEMPERATURE]

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return self.coordinator.data[ATTR_API_DAILY_FORECAST]

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        return self.coordinator.data[ATTR_API_HOURLY_FORECAST]
