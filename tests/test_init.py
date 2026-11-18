"""Setup, entity and config flow tests with a real Home Assistant test instance."""

from __future__ import annotations

import aiohttp
import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.idokep.const import DOMAIN

from .conftest import FIXTURE_TIME

ENTRY_DATA = {"name": "IdokepWeather", "location_name": "Érd"}


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="IdokepWeather",
        data=ENTRY_DATA,
        unique_id="IdokepWeatherUID",
        version=1,
    )


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    entry = _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_setup_and_unload(hass: HomeAssistant, fake_idokep, freezer) -> None:
    """The entry loads, creates the sensors, and unloads."""
    freezer.move_to(FIXTURE_TIME)
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED

    sensors = {s.entity_id: s.state for s in hass.states.async_all("sensor")}
    assert sensors == {
        "sensor.idokepweather_erd_temperature": "14",
        "sensor.idokepweather_erd_condition": "cloudy",
    }

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize("run", range(5))
async def test_weather_entity_survives_setup(
    hass: HomeAssistant, fake_idokep, freezer, run
) -> None:
    """The weather entity always exists after setup (was a race before)."""
    freezer.move_to(FIXTURE_TIME)
    await _setup(hass)

    weather = hass.states.async_all("weather")
    assert len(weather) == 1, hass.states.async_entity_ids()
    assert weather[0].entity_id == "weather.idokepweather_erd_forecast"
    assert weather[0].state == "cloudy"
    assert weather[0].attributes["temperature"] == 14


async def test_entity_settings_survive_reload(
    hass: HomeAssistant, fake_idokep, freezer
) -> None:
    """User changes to entities (here: a new name) are kept on reload."""
    freezer.move_to(FIXTURE_TIME)
    entry = await _setup(hass)
    registry = er.async_get(hass)
    registry.async_update_entity(
        "sensor.idokepweather_erd_temperature", name="Kinti hőmérséklet"
    )

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    entity = registry.async_get("sensor.idokepweather_erd_temperature")
    assert entity is not None
    assert entity.name == "Kinti hőmérséklet"


async def test_connection_error_retries_setup(
    hass: HomeAssistant, fake_idokep, freezer
) -> None:
    """A network error makes Home Assistant retry later instead of crashing."""
    freezer.move_to(FIXTURE_TIME)

    def broken_get(*args, **kwargs):
        raise aiohttp.ClientConnectionError("no network")

    fake_idokep.get = broken_get
    entry = _entry()
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_user_flow_creates_entry(
    hass: HomeAssistant, fake_idokep, freezer
) -> None:
    """The user step stores the name and the location."""
    freezer.move_to(FIXTURE_TIME)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], ENTRY_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "IdokepWeather"
    assert result["data"] == ENTRY_DATA


async def test_second_entry_is_rejected(hass: HomeAssistant) -> None:
    """Today only one location can be configured (fixed unique_id)."""
    _entry().add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Other", "location_name": "Győr"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
