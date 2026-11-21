"""Config flow for Idokep Weather."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_API_LOCATION,
    CONF_FORECAST_DAYS,
    CONF_LOCATION,
    CONF_MEASUREMENT_POINT,
    CONF_POLLEN_CITY,
    CONF_POLLEN_CONFIG_ENTRY,
    CONF_RADAR_CONFIG_ENTRY,
    CONF_SMOG_CITY,
    CONF_SMOG_CONFIG_ENTRY,
    CONF_STATION_CONFIG_ENTRY,
    CONF_STATION_NAME,
    CONF_STATION_UPDATE_INTERVAL,
    CONFIG_FLOW_VERSION,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_STATION_UPDATE_INTERVAL,
    DOMAIN,
    FORECAST_DAYS_CHOICES,
    RADAR_CONFIG_ENTRY_TITLE,
    RADAR_CONFIG_ENTRY_UNIQUE_ID,
    STATION_UPDATE_INTERVAL_CHOICES,
    entry_unique_id,
    station_entry_unique_id,
    weather_unique_id,
)
from .coordinator import (
    BUDAPEST_TZ_NAME,
    FetchPollenCities,
    FetchSmogCities,
    FetchStationWeatherData,
    FetchWeatherData,
    StationDataError,
    async_request_headers,
)

_LOGGER = logging.getLogger(__name__)


class LocationError(Exception):
    """The location can't be used; `error` is the translation key."""

    def __init__(self, error: str, shown: str | None = None) -> None:
        super().__init__(error)
        self.error = error
        self.shown = shown


async def async_validate_location(hass: HomeAssistant, location: str) -> str:
    """Check the location on idokep.hu and return its name as idokep spells it.

    idokep.hu shows Budapest for place names it doesn't know, without an
    error, so the place on the page must match the one the user typed.
    """
    tz = await dt_util.async_get_time_zone(BUDAPEST_TZ_NAME)
    try:
        data = await FetchWeatherData(
            async_get_clientsession(hass),
            location,
            tz,
            tz,
            await async_request_headers(hass),
        )
    except UpdateFailed as err:
        raise LocationError("location_not_found") from err
    except (aiohttp.ClientError, TimeoutError) as err:
        raise LocationError("cannot_connect") from err

    shown = data[ATTR_API_LOCATION]
    if shown is None:
        return location
    if entry_unique_id(shown) != entry_unique_id(location):
        raise LocationError("location_not_found", shown)
    return shown


def _schema(default: str | None = None) -> vol.Schema:
    return vol.Schema(
        {vol.Required(CONF_LOCATION, default=default or vol.UNDEFINED): TextSelector()}
    )


def _station_schema() -> vol.Schema:
    """Return the map station input form."""
    return vol.Schema({vol.Required(CONF_MEASUREMENT_POINT): TextSelector()})


def _city_schema(city_key: str, cities: list[str]) -> vol.Schema:
    """Return an optional city selector populated with available map data."""
    return vol.Schema(
        {
            vol.Optional(city_key): SelectSelector(
                SelectSelectorConfig(
                    options=cities,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


class IdokepConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Idokep: one entry per location."""

    VERSION = CONFIG_FLOW_VERSION

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Create the integration's single global radar entry."""
        if not user_input.get(CONF_RADAR_CONFIG_ENTRY):
            return self.async_abort(reason="not_supported")
        await self.async_set_unique_id(RADAR_CONFIG_ENTRY_UNIQUE_ID)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=RADAR_CONFIG_ENTRY_TITLE,
            data={CONF_RADAR_CONFIG_ENTRY: True},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> IdokepOptionsFlow:
        """Return the options flow."""
        return IdokepOptionsFlow(config_entry)

    async def _async_check(
        self, user_input: dict[str, Any]
    ) -> tuple[str | None, dict[str, str], dict[str, str]]:
        """Validate the location."""
        try:
            name = await async_validate_location(
                self.hass, user_input[CONF_LOCATION].strip()
            )
        except LocationError as err:
            placeholders = {"shown": err.shown or ""}
            error = "location_fallback" if err.shown else err.error
            return None, {"base": error}, placeholders
        return name, {}, {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose the kind of Időkép entry to add."""
        return self.async_show_menu(
            step_id="user", menu_options=["location", "station", "smog", "pollen"]
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a weather location."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}
        if user_input is not None:
            name, errors, placeholders = await self._async_check(user_input)
            if name is not None:
                await self.async_set_unique_id(entry_unique_id(name))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={CONF_LOCATION: name},
                )

        return self.async_show_form(
            step_id="location",
            data_schema=_schema((user_input or {}).get(CONF_LOCATION)),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add one map station as an independent config entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            point = user_input[CONF_MEASUREMENT_POINT].strip()
            if not point:
                errors["base"] = "station_required"
                return self.async_show_form(
                    step_id="station",
                    data_schema=_station_schema(),
                    errors=errors,
                )
            try:
                measurements = await FetchStationWeatherData(
                    async_get_clientsession(self.hass),
                    point,
                    await async_request_headers(self.hass),
                )
            except (aiohttp.ClientError, TimeoutError) as err:
                _LOGGER.warning("Unable to validate Időkép station %r: %s", point, err)
                errors["base"] = "cannot_connect"
            else:
                observation = next(
                    (value for value in measurements.values() if value), None
                )
                if observation is None:
                    errors["base"] = "station_not_found"
                else:
                    station_id = observation.get("station_id")
                    station_name = observation.get("station_name")
                    if (
                        not isinstance(station_id, str)
                        or not station_id.strip()
                        or not isinstance(station_name, str)
                        or not station_name.strip()
                    ):
                        errors["base"] = "station_not_found"
                        return self.async_show_form(
                            step_id="station",
                            data_schema=_station_schema(),
                            errors=errors,
                        )
                    station_id = station_id.strip()
                    station_name = station_name.strip()
                    await self.async_set_unique_id(station_entry_unique_id(station_id))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=station_name,
                        data={
                            CONF_STATION_CONFIG_ENTRY: True,
                            CONF_MEASUREMENT_POINT: station_id,
                            CONF_STATION_NAME: station_name,
                        },
                    )

        return self.async_show_form(
            step_id="station",
            data_schema=_station_schema(),
            errors=errors,
        )

    async def async_step_smog(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a separate smog entry for a selected city."""
        if user_input is None:
            try:
                cities = await FetchSmogCities(
                    async_get_clientsession(self.hass),
                    await async_request_headers(self.hass),
                )
            except (
                aiohttp.ClientError,
                TimeoutError,
                UpdateFailed,
                StationDataError,
            ) as err:
                _LOGGER.warning("Unable to load Időkép smog cities: %s", err)
                return self.async_abort(reason="map_unavailable")
            if not cities:
                return self.async_abort(reason="no_smog_cities")
            self._available_smog_cities = cities
            return self.async_show_form(
                step_id="smog",
                data_schema=_city_schema(CONF_SMOG_CITY, cities),
            )

        city = user_input.get(CONF_SMOG_CITY)
        if not isinstance(city, str) or not city.strip():
            return self.async_abort(reason="city_not_selected")
        city = city.strip()
        if city not in getattr(self, "_available_smog_cities", []):
            return self.async_abort(reason="city_not_available")

        await self.async_set_unique_id(f"smog-{entry_unique_id(city)}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Időkép szmog - {city}",
            data={CONF_SMOG_CONFIG_ENTRY: True, CONF_SMOG_CITY: city},
        )

    async def async_step_pollen(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a separate pollen entry for a selected city."""
        if user_input is None:
            try:
                cities = await FetchPollenCities(
                    async_get_clientsession(self.hass),
                    await async_request_headers(self.hass),
                )
            except (
                aiohttp.ClientError,
                TimeoutError,
                UpdateFailed,
                StationDataError,
            ) as err:
                _LOGGER.warning("Unable to load Időkép pollen cities: %s", err)
                return self.async_abort(reason="map_unavailable")
            if not cities:
                return self.async_abort(reason="no_pollen_cities")
            self._available_pollen_cities = cities
            return self.async_show_form(
                step_id="pollen",
                data_schema=_city_schema(CONF_POLLEN_CITY, cities),
            )

        city = user_input.get(CONF_POLLEN_CITY)
        if not isinstance(city, str) or not city.strip():
            return self.async_abort(reason="city_not_selected")
        city = city.strip()
        if city not in getattr(self, "_available_pollen_cities", []):
            return self.async_abort(reason="city_not_available")

        await self.async_set_unique_id(f"pollen-{entry_unique_id(city)}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Időkép pollen - {city}",
            data={CONF_POLLEN_CONFIG_ENTRY: True, CONF_POLLEN_CITY: city},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Change the location of an existing entry."""
        entry = self._get_reconfigure_entry()
        if (
            entry.data.get(CONF_RADAR_CONFIG_ENTRY)
            or entry.data.get(CONF_STATION_CONFIG_ENTRY)
            or entry.data.get(CONF_SMOG_CONFIG_ENTRY)
            or entry.data.get(CONF_POLLEN_CONFIG_ENTRY)
        ):
            return self.async_abort(reason="not_supported")
        old_location: str = entry.data[CONF_LOCATION]
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        if user_input is not None:
            name, errors, placeholders = await self._async_check(user_input)
            if name is not None:
                new_unique_id = entry_unique_id(name)
                if new_unique_id != entry.unique_id:
                    await self.async_set_unique_id(new_unique_id)
                    self._abort_if_unique_id_configured()
                self._move_weather_entity(entry.entry_id, old_location, name)
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=new_unique_id,
                    title=name if entry.title == old_location else entry.title,
                    data_updates={CONF_LOCATION: name},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(old_location),
            errors=errors,
            description_placeholders=placeholders,
        )

    def _move_weather_entity(self, entry_id: str, old: str, new: str) -> None:
        """Keep the weather entity (and its entity ID) when the location changes.

        Its unique ID contains the location, like in HA-Idokep.
        """
        registry = er.async_get(self.hass)
        entity_id = registry.async_get_entity_id(
            "weather", DOMAIN, weather_unique_id(entry_id, old)
        )
        if entity_id is None:
            return
        new_id = weather_unique_id(entry_id, new)
        if registry.async_get(entity_id).unique_id != new_id:
            registry.async_update_entity(entity_id, new_unique_id=new_id)


class IdokepOptionsFlow(OptionsFlow):
    """Options of one location."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Store the entry explicitly for Home Assistant versions before 2024.11."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose the forecast length for a weather location."""
        if self._config_entry.data.get(CONF_STATION_CONFIG_ENTRY):
            return await self.async_step_station(user_input)
        if self._config_entry.data.get(
            CONF_SMOG_CONFIG_ENTRY
        ) or self._config_entry.data.get(CONF_POLLEN_CONFIG_ENTRY):
            return self.async_abort(reason="sensor_no_options")
        if self._config_entry.data.get(CONF_RADAR_CONFIG_ENTRY):
            return self.async_abort(reason="radar_no_options")
        if user_input is not None:
            options = {CONF_FORECAST_DAYS: int(user_input[CONF_FORECAST_DAYS])}
            return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=self._options_schema(),
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure the refresh interval for one map station."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_STATION_UPDATE_INTERVAL: int(
                        user_input[CONF_STATION_UPDATE_INTERVAL]
                    )
                }
            )

        interval = self._config_entry.options.get(
            CONF_STATION_UPDATE_INTERVAL, DEFAULT_STATION_UPDATE_INTERVAL
        )
        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STATION_UPDATE_INTERVAL, default=str(interval)
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                str(minutes)
                                for minutes in STATION_UPDATE_INTERVAL_CHOICES
                            ],
                            mode=SelectSelectorMode.LIST,
                            translation_key=CONF_STATION_UPDATE_INTERVAL,
                        )
                    )
                }
            ),
        )

    def _options_schema(self, user_input: dict[str, Any] | None = None) -> vol.Schema:
        """Build the options form with the saved values as defaults."""
        current = self._config_entry.options.get(
            CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS
        )
        if user_input is not None:
            current = int(user_input.get(CONF_FORECAST_DAYS, current))
        return vol.Schema(
            {
                vol.Required(CONF_FORECAST_DAYS, default=str(current)): (
                    SelectSelector(
                        SelectSelectorConfig(
                            options=[str(d) for d in FORECAST_DAYS_CHOICES],
                            mode=SelectSelectorMode.LIST,
                            translation_key=CONF_FORECAST_DAYS,
                        )
                    )
                ),
            }
        )
