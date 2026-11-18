"""Binary sensors for the Idokep Weather service."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.weather import (
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import IdokepConfigEntry
from .const import ATTR_API_HOURLY_FORECAST, ATTRIBUTION
from .coordinator import WeatherUpdateCoordinator
from .entity import idokep_device_info

STORM_CONDITIONS = {ATTR_CONDITION_LIGHTNING, ATTR_CONDITION_LIGHTNING_RAINY}

# The keys are part of the unique IDs; they match FabianGabor/HA-Idokep.
CONNECTIVITY = BinarySensorEntityDescription(
    key="idokep_connectivity",
    translation_key="idokep_connectivity",
    device_class=BinarySensorDeviceClass.CONNECTIVITY,
    entity_category=EntityCategory.DIAGNOSTIC,
)
STORM_EXPECTED = BinarySensorEntityDescription(
    key="storm_expected_1h",
    translation_key="storm_expected_1h",
    device_class=BinarySensorDeviceClass.SAFETY,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IdokepConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensors of one location."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            IdokepConnectivitySensor(coordinator, CONNECTIVITY),
            IdokepStormSensor(coordinator, STORM_EXPECTED),
        ]
    )


class IdokepBinarySensor(
    CoordinatorEntity[WeatherUpdateCoordinator], BinarySensorEntity
):
    """Base for Időkép binary sensors."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeatherUpdateCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = idokep_device_info(entry)


class IdokepConnectivitySensor(IdokepBinarySensor):
    """On while the data from idokep.hu is up to date."""

    @property
    def available(self) -> bool:
        """Always available: "off" is the useful state when updates fail."""
        return True

    @property
    def is_on(self) -> bool:
        """Return True if the last update worked."""
        return self.coordinator.last_update_success


def storm_expected(
    hourly_forecast: list[dict], now: datetime, within: timedelta
) -> bool:
    """Return True if a thunderstorm is forecast between now and now + within.

    An hourly forecast covers one hour from its start time, so the current
    hour counts too.
    """
    for forecast in hourly_forecast:
        start = dt_util.parse_datetime(forecast.get("datetime") or "")
        if start is None or forecast.get("condition") not in STORM_CONDITIONS:
            continue
        if start <= now + within and start + timedelta(hours=1) > now:
            return True
    return False


class IdokepStormSensor(IdokepBinarySensor):
    """On if a thunderstorm is forecast for the next hour."""

    @property
    def is_on(self) -> bool:
        """Return True if a thunderstorm is expected within an hour."""
        return storm_expected(
            self.coordinator.data[ATTR_API_HOURLY_FORECAST],
            dt_util.now(),
            timedelta(hours=1),
        )
