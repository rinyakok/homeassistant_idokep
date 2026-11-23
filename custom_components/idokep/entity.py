"""Shared base for Időkép entities."""

from __future__ import annotations

from urllib.parse import quote

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import (
    BASE_IDOKEP_URL,
    CONF_LOCATION,
    CONF_POLLEN_CITY,
    CONF_SMOG_CITY,
    CONF_STATION_NAME,
    DOMAIN,
    MANUFACTURER,
    NAME,
    RADAR_CONFIG_ENTRY_TITLE,
)


def idokep_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device of a location: one device per config entry."""
    location = entry.data[CONF_LOCATION]
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"{NAME} {location}",
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=f"{BASE_IDOKEP_URL}/idojaras/{quote(location)}",
    )


def idokep_station_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device of one independently configured map station."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"{NAME} {entry.data[CONF_STATION_NAME]}",
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=f"{BASE_IDOKEP_URL}/szel",
    )


def idokep_smog_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device of one independently configured smog city."""
    city = entry.data[CONF_SMOG_CITY]
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"{NAME} szmog {city}",
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=f"{BASE_IDOKEP_URL}/szmog",
    )


def idokep_pollen_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return the device of one independently configured pollen city."""
    city = entry.data[CONF_POLLEN_CITY]
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"{NAME} pollen {city}",
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=f"{BASE_IDOKEP_URL}/pollen",
    )


def radar_device_info() -> DeviceInfo:
    """Return the global Időkép radar device."""
    return DeviceInfo(
        identifiers={(DOMAIN, "radar")},
        name=RADAR_CONFIG_ENTRY_TITLE,
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=f"{BASE_IDOKEP_URL}/radar",
    )
