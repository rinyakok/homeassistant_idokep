"""Sensors for the Idokep Weather service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import IdokepConfigEntry, get_entry_data
from .const import (
    ATTR_API_CONDITION,
    ATTR_API_CONDITION_HU,
    ATTR_API_CURRENT,
    ATTR_API_HAZARDS,
    ATTR_API_NATIVE_TEMPERATURE,
    ATTR_API_SHORT_FORECAST,
    ATTR_API_SMOG_SENSORS,
    ATTR_API_STATION_SENSORS,
    ATTR_API_SUNRISE,
    ATTR_API_SUNSET,
    ATTRIBUTION,
    CONF_SMOG_SENSORS_ENABLED,
    CONF_SMOG_STATIONS,
    CONF_STATION_SENSORS_ENABLED,
)
from .coordinator import WeatherUpdateCoordinator
from .entity import idokep_device_info


@dataclass(frozen=True, kw_only=True)
class IdokepSensorEntityDescription(SensorEntityDescription):
    """Describes an Időkép sensor."""

    value_fn: Callable[[dict[str, Any]], StateType | datetime]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _today_hazard(data: dict[str, Any]) -> str | None:
    """Return today's hazard note ("Szeles nap"), or None."""
    today = dt_util.now(dt_util.get_default_time_zone()).date().isoformat()
    notes = [
        h["description"] for h in data.get(ATTR_API_HAZARDS, []) if h["date"] == today
    ]
    return ", ".join(notes) or None


def _current(key: str) -> Callable[[dict[str, Any]], Any]:
    """Return a function that reads one value of the current weather."""
    return lambda data: data[ATTR_API_CURRENT].get(key)


def _station_value(key: str) -> Callable[[dict[str, Any]], Any]:
    """Return one value from a selected map station."""
    return lambda data: (
        data.get(ATTR_API_STATION_SENSORS, {}).get(key, {}).get("value")
        if data.get(ATTR_API_STATION_SENSORS, {}).get(key)
        else None
    )


def _station_attributes(key: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return the location and timestamp for one map station measurement."""

    def attributes(data: dict[str, Any]) -> dict[str, Any]:
        observation = data.get(ATTR_API_STATION_SENSORS, {}).get(key)
        return (
            {name: value for name, value in observation.items() if name != "value"}
            if observation
            else {}
        )

    return attributes


# The keys are part of the unique IDs; they match FabianGabor/HA-Idokep.
SENSOR_TYPES: tuple[IdokepSensorEntityDescription, ...] = (
    IdokepSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_current(ATTR_API_NATIVE_TEMPERATURE),
    ),
    IdokepSensorEntityDescription(
        key="condition",
        translation_key="condition",
        value_fn=_current(ATTR_API_CONDITION),
    ),
    IdokepSensorEntityDescription(
        key="condition_hu",
        translation_key="condition_hu",
        value_fn=_current(ATTR_API_CONDITION_HU),
    ),
    IdokepSensorEntityDescription(
        key="short_forecast",
        translation_key="short_forecast",
        value_fn=_current(ATTR_API_SHORT_FORECAST),
    ),
    IdokepSensorEntityDescription(
        key="sunrise",
        translation_key="sunrise",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_current(ATTR_API_SUNRISE),
    ),
    IdokepSensorEntityDescription(
        key="sunset",
        translation_key="sunset",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_current(ATTR_API_SUNSET),
    ),
    IdokepSensorEntityDescription(
        key="warning_forecast",
        translation_key="warning_forecast",
        value_fn=_today_hazard,
        attributes_fn=lambda data: {"days": data.get(ATTR_API_HAZARDS, [])},
    ),
)

STATION_SENSOR_TYPES: tuple[IdokepSensorEntityDescription, ...] = (
    IdokepSensorEntityDescription(
        key="station_temperature",
        translation_key="station_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_station_value("temperature"),
        attributes_fn=_station_attributes("temperature"),
    ),
    IdokepSensorEntityDescription(
        key="station_precipitation",
        translation_key="station_precipitation",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_station_value("precipitation"),
        attributes_fn=_station_attributes("precipitation"),
    ),
    IdokepSensorEntityDescription(
        key="station_wind_speed",
        translation_key="station_wind_speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_station_value("wind_speed"),
        attributes_fn=_station_attributes("wind_speed"),
    ),
    IdokepSensorEntityDescription(
        key="station_wind_gust",
        translation_key="station_wind_gust",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_station_value("wind_gust"),
        attributes_fn=_station_attributes("wind_gust"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors of one location."""
    coordinator = get_entry_data(hass, entry).coordinator
    descriptions = SENSOR_TYPES
    if entry.options.get(CONF_STATION_SENSORS_ENABLED, False):
        descriptions += STATION_SENSOR_TYPES
    entities: list[SensorEntity] = [
        IdokepSensor(coordinator, description) for description in descriptions
    ]
    if entry.options.get(CONF_SMOG_SENSORS_ENABLED, False):
        for station in entry.data.get(CONF_SMOG_STATIONS, []):
            entities.append(IdokepSmogSensor(coordinator, station, "pm10"))
            if station.get("has_pm25"):
                entities.append(IdokepSmogSensor(coordinator, station, "pm25"))
    async_add_entities(entities)


class IdokepSensor(CoordinatorEntity[WeatherUpdateCoordinator], SensorEntity):
    """An Időkép sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    entity_description: IdokepSensorEntityDescription

    def __init__(
        self,
        coordinator: WeatherUpdateCoordinator,
        description: IdokepSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = idokep_device_info(entry)

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes, if the sensor has any."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)


class IdokepSmogSensor(CoordinatorEntity[WeatherUpdateCoordinator], SensorEntity):
    """A PM10 or PM2.5 measurement from one smog-map station."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "µg/m³"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: WeatherUpdateCoordinator,
        station: dict[str, Any],
        pollutant: str,
    ) -> None:
        """Initialize a station-specific smog sensor."""
        super().__init__(coordinator)
        self._station_id = station["id"]
        self._pollutant = pollutant
        self._station = station
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_smog_{self._station_id}_{pollutant}"
        )
        pollutant_name = "PM10" if pollutant == "pm10" else "PM2.5"
        self._attr_name = f"{station['name']} {pollutant_name}"
        self._attr_device_info = idokep_device_info(coordinator.config_entry)

    @property
    def native_value(self) -> StateType:
        """Return the latest pollutant measurement."""
        observation = self.coordinator.data.get(ATTR_API_SMOG_SENSORS, {}).get(
            self._station_id
        )
        return observation.get(self._pollutant) if observation else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return station and measurement metadata."""
        observation = self.coordinator.data.get(ATTR_API_SMOG_SENSORS, {}).get(
            self._station_id
        )
        if observation is None:
            return {
                "station_id": self._station_id,
                "station_name": self._station["name"],
                "city": self._station["city"],
            }
        return {
            "station_id": observation["id"],
            "station_name": observation["name"],
            "city": observation["city"],
            "source": observation["source"],
            "latitude": observation["latitude"],
            "longitude": observation["longitude"],
            "measured_at": observation["measured_at"],
        }
