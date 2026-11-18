"""Sensors for the Idokep Weather service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IdokepConfigEntry
from .const import (
    ATTR_API_CONDITION,
    ATTR_API_CURRENT,
    ATTR_API_NATIVE_TEMPERATURE,
    ATTRIBUTION,
)
from .coordinator import WeatherUpdateCoordinator
from .entity import idokep_device_info


@dataclass(frozen=True, kw_only=True)
class IdokepSensorEntityDescription(SensorEntityDescription):
    """Describes an Időkép sensor."""

    value_fn: Callable[[dict[str, Any]], StateType]


# The keys are part of the unique IDs; they match FabianGabor/HA-Idokep.
SENSOR_TYPES: tuple[IdokepSensorEntityDescription, ...] = (
    IdokepSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data[ATTR_API_CURRENT][ATTR_API_NATIVE_TEMPERATURE],
    ),
    IdokepSensorEntityDescription(
        key="condition",
        translation_key="condition",
        value_fn=lambda data: data[ATTR_API_CURRENT][ATTR_API_CONDITION],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors of one location."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        IdokepSensor(coordinator, description) for description in SENSOR_TYPES
    )


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
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
