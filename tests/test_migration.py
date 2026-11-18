"""Migration of version 1 entries: entity IDs must not change."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.idokep.const import DOMAIN

from .conftest import FIXTURE_TIME


@pytest.fixture(autouse=True)
def _frozen_time(freezer):
    freezer.move_to(FIXTURE_TIME)


def _device(hass: HomeAssistant, identifier: str) -> dr.DeviceEntry:
    """Return the Időkép device with this identifier."""
    (device,) = [
        d for d in dr.async_get(hass).devices if (DOMAIN, identifier) in d.identifiers
    ]
    return device


def _register(hass, entry, platform_domain, unique_id, object_id):
    return er.async_get(hass).async_get_or_create(
        platform_domain,
        DOMAIN,
        unique_id,
        config_entry=entry,
        suggested_object_id=object_id,
    )


def _entities(hass: HomeAssistant, entry: MockConfigEntry) -> dict[str, str]:
    registry = er.async_get(hass)
    return {
        e.entity_id: e.unique_id
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    }


async def test_migrate_single_location_entry(hass: HomeAssistant, fake_idokep) -> None:
    """An entry of this integration from before multiple locations."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="IdokepWeather",
        data={"name": "IdokepWeather", "location_name": "Érd"},
        unique_id="IdokepWeatherUID",
        version=1,
        entry_id="legacy",
    )
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "IdokepWeatherUID")},
        name="IdokepWeather",
    )
    dr.async_get(hass).async_update_device(device.id, area_id="kert")
    _register(
        hass,
        entry,
        "sensor",
        "IdokepWeatherUID_native_temperature",
        "idokepweather_erd_temperature",
    )
    _register(
        hass,
        entry,
        "sensor",
        "IdokepWeatherUID_condition",
        "idokepweather_erd_condition",
    )
    _register(hass, entry, "weather", "IdokepWeatherUID", "idokepweather_erd_forecast")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.version == 2
    assert entry.data == {"location": "Érd"}
    assert entry.unique_id == "erd"
    assert entry.title == "Érd"
    # Same entity IDs as before, now with the new unique IDs, no extras.
    assert _entities(hass, entry) == {
        "sensor.idokepweather_erd_temperature": "legacy_temperature",
        "sensor.idokepweather_erd_condition": "legacy_condition",
        "weather.idokepweather_erd_forecast": "legacy_weather_erd",
    }
    assert hass.states.get("weather.idokepweather_erd_forecast").state == "cloudy"
    assert hass.states.get("sensor.idokepweather_erd_temperature").state == "14"
    # The device is kept (with its area), under the new identifier.
    moved = dr.async_get(hass).async_get(device.id)
    assert moved.identifiers == {(DOMAIN, "legacy")}
    assert moved.area_id == "kert"


async def test_migrate_keeps_custom_title(hass: HomeAssistant, fake_idokep) -> None:
    """A title the user chose is kept."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Otthon",
        data={"name": "Otthon", "location_name": "Érd"},
        unique_id="IdokepWeatherUID",
        version=1,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)

    assert entry.title == "Otthon"


async def test_switch_from_ha_idokep(hass: HomeAssistant, fake_idokep) -> None:
    """An entry made by FabianGabor/HA-Idokep keeps all its entity IDs."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Érd",
        data={"location": "Érd"},
        unique_id="erd",
        version=1,
        entry_id="fabian",
    )
    entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "fabian")},
        name="Időkép",
    )
    _register(hass, entry, "sensor", "fabian_temperature", "idokep_temperature")
    _register(hass, entry, "sensor", "fabian_condition", "idokep_weather_condition")
    _register(hass, entry, "weather", "fabian_weather_erd", "idokep_erd")

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.version == 2
    assert entry.data == {"location": "Érd"}
    assert _entities(hass, entry) == {
        "sensor.idokep_temperature": "fabian_temperature",
        "sensor.idokep_weather_condition": "fabian_condition",
        "weather.idokep_erd": "fabian_weather_erd",
    }
    assert hass.states.get("weather.idokep_erd").state == "cloudy"
    assert hass.states.get("sensor.idokep_temperature").state == "14"
    assert _device(hass, "fabian").id == (device.id)


async def test_entry_from_a_newer_version_is_not_loaded(hass: HomeAssistant) -> None:
    """A downgrade from a future version is refused instead of breaking data."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={"location": "Érd"}, unique_id="erd", version=3
    )
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.MIGRATION_ERROR
