"""The Idokep Weather component."""
# BASED ON https://github.com/home-assistant/core/blob/dev/homeassistant/components/openweathermap/

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODE,
    CONF_NAME,
    ATTR_LOCATION,
)
from homeassistant.core import HomeAssistant

from .const import CONFIG_FLOW_VERSION, PLATFORMS, DEFAULT_LANGUAGE, ATTR_API_LOCATION
from .coordinator import WeatherUpdateCoordinator

from typing import Any
OPTION_DEFAULTS = {CONF_LANGUAGE: DEFAULT_LANGUAGE}

_LOGGER = logging.getLogger(__name__)


@dataclass
class IdokepData:
    """Runtime data definition."""

    name: str
    coordinator: WeatherUpdateCoordinator

type IdokepConfigEntry = ConfigEntry[IdokepData]

def build_data_and_options(combined_data: dict[str, Any],) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split combined data and options."""
    data = {k: v for k, v in combined_data.items() if k not in OPTION_DEFAULTS}
    options = {
        option: combined_data.get(option, default)
        for option, default in OPTION_DEFAULTS.items()
    }
    return (data, options)


async def async_setup_entry(hass: HomeAssistant, entry: IdokepConfigEntry) -> bool:
    """Set up IdokepWeather as config entry."""
    _LOGGER.debug("ENTRY: %s", str(entry))
    name = entry.data[CONF_NAME]
    location = entry.data.get(ATTR_API_LOCATION)

    weather_coordinator = WeatherUpdateCoordinator(location, hass)

    await weather_coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    entry.runtime_data = IdokepData(name, weather_coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    config_entries = hass.config_entries
    data = entry.data
    options = entry.options
    version = entry.version

    _LOGGER.debug("Migrating Idokep Weather entry from version %s", version)

    if version < 1:
        combined_data = {**data, **options}
        new_data, new_options = build_data_and_options(combined_data)
        config_entries.async_update_entry(
            entry,
            data=new_data,
            options=new_options,
            version=CONFIG_FLOW_VERSION,
        )

    _LOGGER.debug("Migration to version %s successful", CONFIG_FLOW_VERSION)

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: IdokepData) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)