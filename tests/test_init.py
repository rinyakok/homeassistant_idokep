"""Setup, entity and config flow tests with a real Home Assistant test instance."""

from __future__ import annotations

import aiohttp
import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.idokep.const import DOMAIN

from .conftest import FIXTURE_TIME, FakeClientSession, load_fixture, pages_with_alerts


@pytest.fixture(autouse=True)
def _frozen_time(freezer):
    """All tests run at the moment the pages were saved."""
    freezer.move_to(FIXTURE_TIME)


def _device(hass: HomeAssistant, identifier: str) -> dr.DeviceEntry:
    """Return the Időkép device with this identifier."""
    (device,) = [
        d for d in dr.async_get(hass).devices if (DOMAIN, identifier) in d.identifiers
    ]
    return device


def _entry(location: str = "Érd", unique_id: str = "erd") -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title=location,
        data={"location": location},
        unique_id=unique_id,
        version=2,
    )


async def _setup(hass: HomeAssistant, entry: MockConfigEntry | None = None):
    entry = entry or _entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _start_user_flow(hass: HomeAssistant, location: str):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"location": location}
    )


# --- Entities ----------------------------------------------------------------


async def test_entities_of_a_new_location(hass: HomeAssistant, fake_idokep) -> None:
    """A location gets one device with a weather entity and two sensors."""
    entry = await _setup(hass)
    assert entry.state is ConfigEntryState.LOADED

    assert hass.states.get("weather.idokep_erd").state == "cloudy"
    assert hass.states.get("weather.idokep_erd").attributes["temperature"] == 14
    assert hass.states.get("sensor.idokep_erd_temperature").state == "14"
    assert hass.states.get("sensor.idokep_erd_condition").state == "cloudy"

    registry = er.async_get(hass)
    assert {
        e.unique_id: e.entity_id
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
    } == {
        f"{entry.entry_id}_temperature": "sensor.idokep_erd_temperature",
        f"{entry.entry_id}_condition": "sensor.idokep_erd_condition",
        f"{entry.entry_id}_condition_hu": "sensor.idokep_erd_condition_hungarian",
        f"{entry.entry_id}_short_forecast": "sensor.idokep_erd_short_forecast",
        f"{entry.entry_id}_sunrise": "sensor.idokep_erd_sunrise",
        f"{entry.entry_id}_sunset": "sensor.idokep_erd_sunset",
        f"{entry.entry_id}_idokep_connectivity": "binary_sensor.idokep_erd_connection",
        f"{entry.entry_id}_storm_expected_1h": (
            "binary_sensor.idokep_erd_storm_in_the_next_hour"
        ),
        f"{entry.entry_id}_warning_forecast": "sensor.idokep_erd_warning_forecast",
        f"{entry.entry_id}_weather_alert": "binary_sensor.idokep_erd_weather_alert",
        f"{entry.entry_id}_alert_yellow": "binary_sensor.idokep_erd_yellow_alert",
        f"{entry.entry_id}_alert_orange": "binary_sensor.idokep_erd_orange_alert",
        f"{entry.entry_id}_alert_red": "binary_sensor.idokep_erd_red_alert",
        f"{entry.entry_id}_weather_erd": "weather.idokep_erd",
    }

    device = _device(hass, entry.entry_id)
    assert device.name == "Időkép Érd"
    assert device.configuration_url == "https://www.idokep.hu/idojaras/%C3%89rd"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_two_locations(hass: HomeAssistant, fake_idokep) -> None:
    """Several locations work side by side."""
    await _setup(hass)
    await _setup(hass, _entry("Győr", "gyor"))

    assert hass.states.get("weather.idokep_erd") is not None
    assert hass.states.get("weather.idokep_gyor") is not None
    assert hass.states.get("sensor.idokep_gyor_temperature").state == "14"
    assert any(url.endswith("/Győr") for url in fake_idokep.requested)


@pytest.mark.parametrize("run", range(5))
async def test_weather_entity_survives_setup(
    hass: HomeAssistant, fake_idokep, run
) -> None:
    """The weather entity always exists after setup (was a race before)."""
    await _setup(hass)
    assert hass.states.get("weather.idokep_erd") is not None


async def test_entity_settings_survive_reload(hass: HomeAssistant, fake_idokep) -> None:
    """User changes to entities (here: a new name) are kept on reload."""
    entry = await _setup(hass)
    registry = er.async_get(hass)
    registry.async_update_entity(
        "sensor.idokep_erd_temperature", name="Kinti hőmérséklet"
    )

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert registry.async_get("sensor.idokep_erd_temperature").name == (
        "Kinti hőmérséklet"
    )


async def test_connection_error_retries_setup(hass: HomeAssistant, fake_idokep) -> None:
    """A network error makes Home Assistant retry later instead of crashing."""
    fake_idokep.error = aiohttp.ClientConnectionError("no network")
    entry = _entry()
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_unknown_location_is_logged(
    hass: HomeAssistant, monkeypatch, caplog
) -> None:
    """An existing entry whose place idokep doesn't know logs a warning once."""
    budapest = load_fixture("idojaras.html").replace(
        "Érd időjárás", "Budapest időjárás"
    )
    session = FakeClientSession(
        {"/idojaras/": budapest, "/elorejelzes/": load_fixture("elorejelzes.html")}
    )
    monkeypatch.setattr(
        "custom_components.idokep.coordinator.async_get_clientsession",
        lambda hass: session,
    )
    entry = await _setup(hass)
    await entry.runtime_data.coordinator.async_refresh()

    assert caplog.text.count("does not know the location 'Érd'") == 1


# --- Adding a location -------------------------------------------------------


async def test_user_flow_uses_idokep_spelling(hass: HomeAssistant, fake_idokep) -> None:
    """The place name is stored as idokep.hu writes it."""
    fake_idokep.pages["/idojaras/"] = load_fixture("idojaras.html")
    fake_idokep.echo_location = False  # "erd" shows the Érd page

    result = await _start_user_flow(hass, " erd ")

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Érd"
    assert result["data"] == {"location": "Érd"}
    assert result["result"].unique_id == "erd"
    await hass.async_block_till_done()
    assert hass.states.get("weather.idokep_erd") is not None


async def test_user_flow_place_unknown_to_idokep(hass: HomeAssistant) -> None:
    """idokep.hu shows Budapest for unknown places; the flow says so."""
    budapest = load_fixture("idojaras.html").replace(
        "Érd időjárás", "Budapest időjárás"
    )
    session = FakeClientSession(
        {"/idojaras/": budapest, "/elorejelzes/": load_fixture("elorejelzes.html")}
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "custom_components.idokep.config_flow.async_get_clientsession",
            lambda hass: session,
        )
        result = await _start_user_flow(hass, "Nincsilyenhely")

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "location_fallback"}
    assert result["description_placeholders"] == {"shown": "Budapest"}


async def test_user_flow_no_weather_data(hass: HomeAssistant, fake_idokep) -> None:
    """A page without weather data gives a clear error."""
    empty = "<html><head><title>Hiba</title></head><body></body></html>"
    fake_idokep.pages = {"/idojaras/": empty, "/elorejelzes/": empty}

    result = await _start_user_flow(hass, "Érd")

    assert result["errors"] == {"base": "location_not_found"}


async def test_user_flow_cannot_connect(hass: HomeAssistant, fake_idokep) -> None:
    """A network error gives a clear error and the form again."""
    fake_idokep.error = aiohttp.ClientConnectionError("no network")

    result = await _start_user_flow(hass, "Érd")

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_same_location_twice(hass: HomeAssistant, fake_idokep) -> None:
    """The same place can't be added twice."""
    _entry().add_to_hass(hass)

    result = await _start_user_flow(hass, "Érd")

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# --- Changing the location ---------------------------------------------------


async def _reconfigure(hass: HomeAssistant, entry: MockConfigEntry, location: str):
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"location": location}
    )
    await hass.async_block_till_done()
    return result


async def test_reconfigure_keeps_entity_ids(hass: HomeAssistant, fake_idokep) -> None:
    """A new location keeps the entity IDs, so automations keep working."""
    entry = await _setup(hass)

    result = await _reconfigure(hass, entry, "Győr")

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {"location": "Győr"}
    assert entry.title == "Győr"
    assert entry.unique_id == "gyor"
    registry = er.async_get(hass)
    weather = registry.async_get("weather.idokep_erd")
    assert weather.unique_id == f"{entry.entry_id}_weather_gyor"
    assert len(er.async_entries_for_config_entry(registry, entry.entry_id)) == 14
    assert hass.states.get("weather.idokep_erd") is not None
    assert fake_idokep.requested[-1].endswith("/elorejelzes/Győr")


async def test_reconfigure_to_existing_location(
    hass: HomeAssistant, fake_idokep
) -> None:
    """A location that already has its own entry can't be chosen."""
    entry = await _setup(hass)
    _entry("Győr", "gyor").add_to_hass(hass)

    result = await _reconfigure(hass, entry, "Győr")

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data == {"location": "Érd"}


async def test_reconfigure_error_shows_form(hass: HomeAssistant, fake_idokep) -> None:
    """A network error during reconfigure shows the form with the error."""
    entry = await _setup(hass)
    fake_idokep.error = aiohttp.ClientConnectionError("no network")

    result = await _reconfigure(hass, entry, "Győr")

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reconfigure_same_place_other_spelling(
    hass: HomeAssistant, fake_idokep
) -> None:
    """Typing the same place differently keeps everything as it is."""
    entry = await _setup(hass)

    result = await _reconfigure(hass, entry, "ÉRD")

    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == "erd"
    weather = er.async_get(hass).async_get("weather.idokep_erd")
    assert weather.unique_id == f"{entry.entry_id}_weather_erd"


# --- New sensors -------------------------------------------------------------


async def test_new_sensor_states(hass: HomeAssistant, fake_idokep) -> None:
    """Hungarian condition, short forecast, sun times and binary sensors."""
    await _setup(hass)

    assert hass.states.get("sensor.idokep_erd_condition_hungarian").state == (
        "Erősen felhős"
    )
    assert hass.states.get("sensor.idokep_erd_short_forecast").state == (
        "Kettősfronti hatás várható"
    )
    assert hass.states.get("sensor.idokep_erd_sunrise").state == (
        "2026-11-18T05:54:00+00:00"
    )
    assert hass.states.get("sensor.idokep_erd_sunset").state == (
        "2026-11-18T15:05:00+00:00"
    )
    assert hass.states.get("binary_sensor.idokep_erd_connection").state == "on"
    assert (
        hass.states.get("binary_sensor.idokep_erd_storm_in_the_next_hour").state
        == "off"
    )


async def test_weather_extra_attributes(hass: HomeAssistant, fake_idokep) -> None:
    """Short forecast and the rain of the current hour, as in HA-Idokep."""
    await _setup(hass)

    attributes = hass.states.get("weather.idokep_erd").attributes
    assert attributes["short_forecast"] == "Kettősfronti hatás várható"
    assert attributes["precipitation"] == 0.0
    assert attributes["precipitation_probability"] == 0


async def test_connection_sensor_turns_off(hass: HomeAssistant, fake_idokep) -> None:
    """When updates fail, the connection sensor is off but still available."""
    entry = await _setup(hass)
    fake_idokep.error = aiohttp.ClientConnectionError("no network")

    await entry.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.idokep_erd_connection").state == "off"
    assert hass.states.get("sensor.idokep_erd_temperature").state == "unavailable"


# --- Weather alerts ----------------------------------------------------------


async def test_warning_forecast_sensor(hass: HomeAssistant, fake_idokep) -> None:
    """Today's hazard note is the state; all days are in the attributes."""
    await _setup(hass)

    state = hass.states.get("sensor.idokep_erd_warning_forecast")
    assert state.state == "Hidegfront erős széllel"
    assert [day["description"] for day in state.attributes["days"]][:3] == [
        "Hidegfront erős széllel",
        "Sok eső",
        "Szeles nap",
    ]


async def test_alert_sensors_on_a_calm_day(hass: HomeAssistant, fake_idokep) -> None:
    """Without alerts every alert sensor is off."""
    await _setup(hass)

    for level in ("weather", "yellow", "orange", "red"):
        assert hass.states.get(f"binary_sensor.idokep_erd_{level}_alert").state == (
            "off"
        )
    assert hass.states.get("binary_sensor.idokep_erd_weather_alert").attributes[
        "alert_count"
    ] == (0)


async def test_alert_sensors(hass: HomeAssistant, fake_idokep) -> None:
    """Alert sensors and their attributes (same as HA-Idokep)."""
    fake_idokep.pages = pages_with_alerts()
    fake_idokep.echo_location = False
    await _setup(hass)

    alert = hass.states.get("binary_sensor.idokep_erd_weather_alert")
    assert alert.state == "on"
    assert alert.attributes["alert_count"] == 3
    assert alert.attributes["yellow_alerts"] == 1
    assert alert.attributes["orange_alerts"] == 1
    assert alert.attributes["red_alerts"] == 1
    assert alert.attributes["alerts"][0] == {
        "level": "yellow",
        "type": "wind",
        "description": "Sárga riasztás szélre",
        "icon_url": None,
    }

    orange = hass.states.get("binary_sensor.idokep_erd_orange_alert")
    assert orange.state == "on"
    assert orange.attributes == orange.attributes | {
        "alert_count": 1,
        "alerts": [
            {
                "type": "thunderstorm",
                "description": "Narancs riasztás zivatar",
                "icon_url": "https://www.idokep.hu/images/alerts/thunder.png",
            }
        ],
    }
    assert hass.states.get("binary_sensor.idokep_erd_red_alert").state == "on"


# --- Options -----------------------------------------------------------------


async def _daily_forecast(hass: HomeAssistant) -> list[dict]:
    response = await hass.services.async_call(
        "weather",
        "get_forecasts",
        {"entity_id": "weather.idokep_erd", "type": "daily"},
        blocking=True,
        return_response=True,
    )
    return response["weather.idokep_erd"]["forecast"]


async def test_options_30_day_forecast(hass: HomeAssistant, fake_idokep) -> None:
    """Choosing 30 days reloads the entry with a 30-day daily forecast."""
    entry = await _setup(hass)
    assert len(await _daily_forecast(hass)) == 15

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"forecast_days": "30"}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {"forecast_days": 30}
    assert len(await _daily_forecast(hass)) == 30
    assert any("/30napos/" in url for url in fake_idokep.requested)
