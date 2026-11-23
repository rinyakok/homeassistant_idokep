"""The Idokep Weather component."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_LOCATION,
    CONF_POLLEN_CONFIG_ENTRY,
    CONF_RADAR_CONFIG_ENTRY,
    CONF_SMOG_CONFIG_ENTRY,
    CONF_STATION_CONFIG_ENTRY,
    CONFIG_FLOW_VERSION,
    DOMAIN,
    LEGACY_CONF_LOCATION,
    LEGACY_DEFAULT_TITLE,
    LEGACY_UNIQUE_ID,
    PLATFORMS,
    POLLEN_PLATFORMS,
    RADAR_PLATFORMS,
    SMOG_PLATFORMS,
    STATION_PLATFORMS,
    entry_unique_id,
    weather_unique_id,
)
from .coordinator import (
    PollenUpdateCoordinator,
    SmogUpdateCoordinator,
    StationUpdateCoordinator,
    WeatherUpdateCoordinator,
)
from .radar import RadarUpdateCoordinator

_LOGGER = logging.getLogger(__name__)
DATA_RUNTIME = f"{DOMAIN}_runtime"
DATA_STATION_RUNTIME = f"{DOMAIN}_station_runtime"
DATA_SMOG_RUNTIME = f"{DOMAIN}_smog_runtime"
DATA_POLLEN_RUNTIME = f"{DOMAIN}_pollen_runtime"
DATA_RADAR = f"{DOMAIN}_radar"


@dataclass
class IdokepData:
    """Runtime data definition."""

    coordinator: WeatherUpdateCoordinator


@dataclass
class IdokepStationData:
    """Runtime data for one station config entry."""

    coordinator: StationUpdateCoordinator


@dataclass
class IdokepSmogData:
    """Runtime data for one smog city config entry."""

    coordinator: SmogUpdateCoordinator


@dataclass
class IdokepPollenData:
    """Runtime data for one pollen city config entry."""

    coordinator: PollenUpdateCoordinator


IdokepConfigEntry = ConfigEntry


def get_entry_data(hass: HomeAssistant, entry: ConfigEntry) -> IdokepData:
    """Return the runtime data for a config entry."""
    return hass.data[DATA_RUNTIME][entry.entry_id]


def get_station_data(hass: HomeAssistant, entry: ConfigEntry) -> IdokepStationData:
    """Return the runtime data for a station config entry."""
    return hass.data[DATA_STATION_RUNTIME][entry.entry_id]


def get_smog_data(hass: HomeAssistant, entry: ConfigEntry) -> IdokepSmogData:
    """Return the runtime data for a smog config entry."""
    return hass.data[DATA_SMOG_RUNTIME][entry.entry_id]


def get_pollen_data(hass: HomeAssistant, entry: ConfigEntry) -> IdokepPollenData:
    """Return the runtime data for a pollen config entry."""
    return hass.data[DATA_POLLEN_RUNTIME][entry.entry_id]


async def async_setup_entry(hass: HomeAssistant, entry: IdokepConfigEntry) -> bool:
    """Set up one Időkép location."""
    if entry.data.get(CONF_SMOG_CONFIG_ENTRY):
        coordinator = SmogUpdateCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data.setdefault(DATA_SMOG_RUNTIME, {})[entry.entry_id] = IdokepSmogData(
            coordinator
        )
        await hass.config_entries.async_forward_entry_setups(entry, SMOG_PLATFORMS)
        return True

    if entry.data.get(CONF_POLLEN_CONFIG_ENTRY):
        coordinator = PollenUpdateCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data.setdefault(DATA_POLLEN_RUNTIME, {})[entry.entry_id] = (
            IdokepPollenData(coordinator)
        )
        await hass.config_entries.async_forward_entry_setups(entry, POLLEN_PLATFORMS)
        return True

    if entry.data.get(CONF_STATION_CONFIG_ENTRY):
        coordinator = StationUpdateCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data.setdefault(DATA_STATION_RUNTIME, {})[entry.entry_id] = (
            IdokepStationData(coordinator)
        )
        entry.async_on_unload(entry.add_update_listener(_async_reload_on_change))
        await hass.config_entries.async_forward_entry_setups(entry, STATION_PLATFORMS)
        return True

    if entry.data.get(CONF_RADAR_CONFIG_ENTRY):
        coordinator = RadarUpdateCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
        hass.data.setdefault(DATA_RADAR, {})[entry.entry_id] = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, RADAR_PLATFORMS)
        return True

    coordinator = WeatherUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DATA_RUNTIME, {})[entry.entry_id] = IdokepData(coordinator)
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_change))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


def get_radar_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> RadarUpdateCoordinator:
    """Return the global radar coordinator for its config entry."""
    return hass.data[DATA_RADAR][entry.entry_id]


async def _async_reload_on_change(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: IdokepConfigEntry) -> bool:
    """Unload a config entry."""
    if entry.data.get(CONF_SMOG_CONFIG_ENTRY):
        unloaded = await hass.config_entries.async_unload_platforms(
            entry, SMOG_PLATFORMS
        )
        if unloaded:
            hass.data[DATA_SMOG_RUNTIME].pop(entry.entry_id, None)
        return unloaded

    if entry.data.get(CONF_POLLEN_CONFIG_ENTRY):
        unloaded = await hass.config_entries.async_unload_platforms(
            entry, POLLEN_PLATFORMS
        )
        if unloaded:
            hass.data[DATA_POLLEN_RUNTIME].pop(entry.entry_id, None)
        return unloaded

    if entry.data.get(CONF_STATION_CONFIG_ENTRY):
        unloaded = await hass.config_entries.async_unload_platforms(
            entry, STATION_PLATFORMS
        )
        if unloaded:
            hass.data[DATA_STATION_RUNTIME].pop(entry.entry_id, None)
        return unloaded

    if entry.data.get(CONF_RADAR_CONFIG_ENTRY):
        unloaded = await hass.config_entries.async_unload_platforms(
            entry, RADAR_PLATFORMS
        )
        if unloaded:
            hass.data[DATA_RADAR].pop(entry.entry_id, None)
        return unloaded

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DATA_RUNTIME].pop(entry.entry_id, None)
    return unloaded


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to version 2.

    Two kinds of version 1 entries exist with this domain:
    - this integration before multiple locations: data {"name", "location_name"},
      fixed unique IDs ("IdokepWeatherUID...");
    - FabianGabor/HA-Idokep: data {"location"}, unique IDs already in the
      version 2 format.
    Entity IDs stay the same in both cases, so dashboards and automations
    keep working.
    """
    if entry.version > CONFIG_FLOW_VERSION:
        # Downgrade from a future version: not supported.
        return False

    if entry.version == 1:
        if LEGACY_CONF_LOCATION in entry.data:
            await _migrate_legacy_entry(hass, entry)
        else:
            hass.config_entries.async_update_entry(entry, version=2)
        _LOGGER.info("Migrated Időkép entry %s to version 2", entry.data[CONF_LOCATION])
    return True


async def _migrate_legacy_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Move a single-location entry of this integration to version 2."""
    location: str = entry.data[LEGACY_CONF_LOCATION]
    new_unique_ids = {
        f"{LEGACY_UNIQUE_ID}_native_temperature": f"{entry.entry_id}_temperature",
        f"{LEGACY_UNIQUE_ID}_condition": f"{entry.entry_id}_condition",
        LEGACY_UNIQUE_ID: weather_unique_id(entry.entry_id, location),
    }

    @callback
    def _new_unique_id(entity: er.RegistryEntry) -> dict | None:
        if entity.unique_id in new_unique_ids:
            return {"new_unique_id": new_unique_ids[entity.unique_id]}
        return None

    await er.async_migrate_entries(hass, entry.entry_id, _new_unique_id)

    # Keep the existing device (and its area) by moving it to the new ID.
    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        if (DOMAIN, LEGACY_UNIQUE_ID) in device.identifiers:
            device_registry.async_update_device(
                device.id, new_identifiers={(DOMAIN, entry.entry_id)}
            )

    hass.config_entries.async_update_entry(
        entry,
        data={CONF_LOCATION: location},
        unique_id=entry_unique_id(location),
        # Keep a title the user chose; replace the old default name.
        title=location if entry.title == LEGACY_DEFAULT_TITLE else entry.title,
        version=2,
    )
