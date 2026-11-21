"""Shared base for Időkép entities."""

from __future__ import annotations

from urllib.parse import quote

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo

from .const import (
    BASE_IDOKEP_URL,
    CONF_LOCATION,
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


def radar_device_info() -> DeviceInfo:
    """Return the global Időkép radar device."""
    return DeviceInfo(
        identifiers={(DOMAIN, "radar")},
        name=RADAR_CONFIG_ENTRY_TITLE,
        manufacturer=MANUFACTURER,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=f"{BASE_IDOKEP_URL}/radar",
    )
