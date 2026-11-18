"""The Idokep Weather component."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .const import ATTR_API_LOCATION, PLATFORMS
from .coordinator import WeatherUpdateCoordinator


@dataclass
class IdokepData:
    """Runtime data definition."""

    name: str
    coordinator: WeatherUpdateCoordinator


type IdokepConfigEntry = ConfigEntry[IdokepData]


async def async_setup_entry(hass: HomeAssistant, entry: IdokepConfigEntry) -> bool:
    """Set up IdokepWeather as config entry."""
    weather_coordinator = WeatherUpdateCoordinator(
        entry.data.get(ATTR_API_LOCATION), hass
    )
    await weather_coordinator.async_config_entry_first_refresh()

    entry.runtime_data = IdokepData(entry.data[CONF_NAME], weather_coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: IdokepConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
