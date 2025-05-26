"""Support for the Idokep Wetaher service."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UV_INDEX,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import IdokepConfigEntry
from .const import (
    ATTR_API_CONDITION,
    ATTR_API_CURRENT,
    ATTR_API_NATIVE_TEMPERATURE,
    ATTR_API_NATIVE_TEMPERATURE_UNIT,
    ATTR_API_WEATHER,
    ATTR_API_LOCATION,
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import WeatherUpdateCoordinator

WEATHER_SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    #  SensorEntityDescription(
    #      key=ATTR_API_WEATHER,
    #      name="Weather",
    #  ),
    SensorEntityDescription(
        key=ATTR_API_NATIVE_TEMPERATURE,
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_API_CONDITION,
        name="Condition",
    ),
)

async def async_setup_entry(hass: HomeAssistant, config_entry: IdokepConfigEntry, async_add_entities: AddEntitiesCallback,) -> None:
    """Set up IdokepWeather sensor entities based on a config entry."""
    domain_data = config_entry.runtime_data
    name = domain_data.name
    unique_id = config_entry.unique_id
    assert unique_id is not None
    weather_coordinator = domain_data.coordinator

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    for entry in entries:
        entity_registry.async_remove(entry.entity_id)


    name_part_location = location = config_entry.data.get(ATTR_API_LOCATION)
    async_add_entities(
        IdokepSensor(
            name_part_location,
            unique_id,
            description,
            weather_coordinator,
        )
        for description in WEATHER_SENSOR_TYPES
    )
    

class AbstractIdokepSensor(SensorEntity):
    """Abstract class for an Idokep sensor."""

    _attr_should_poll = False
    _attr_attribution = ATTRIBUTION

    def __init__(self, name: str, unique_id: str, description: SensorEntityDescription, coordinator: DataUpdateCoordinator, ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._coordinator = coordinator

        self._attr_name = f"{name}_{description.name}"
        self._attr_unique_id = f"{unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{unique_id}")},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Get the latest data from OWM and updates the states."""
        await self._coordinator.async_request_refresh()


class IdokepSensor(AbstractIdokepSensor):
    """Implementation of an Idokep sensor."""

    def __init__( self, name: str, unique_id: str, description: SensorEntityDescription, weather_coordinator: WeatherUpdateCoordinator, ) -> None:
        """Initialize the sensor."""
        super().__init__(name, unique_id, description, weather_coordinator)
        self._weather_coordinator = weather_coordinator

    @property
    def native_value(self) -> StateType:
        """Return the state of the device."""
        return self._weather_coordinator.data[ATTR_API_CURRENT].get(
            self.entity_description.key
        )
    
