"""Config flow for Idokep Weather."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
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
    CONF_POLLEN_LOCATION,
    CONF_POLLEN_SENSORS_ENABLED,
    CONF_SMOG_SENSORS_ENABLED,
    CONF_SMOG_STATIONS,
    CONF_STATION_CONFIG_ENTRY,
    CONF_STATION_NAME,
    CONF_STATION_UPDATE_INTERVAL,
    CONFIG_FLOW_VERSION,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_STATION_UPDATE_INTERVAL,
    DOMAIN,
    FORECAST_DAYS_CHOICES,
    STATION_UPDATE_INTERVAL_CHOICES,
    entry_unique_id,
    station_entry_unique_id,
    weather_unique_id,
)
from .coordinator import (
    BUDAPEST_TZ_NAME,
    FetchPollenLocation,
    FetchSmogStations,
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


class IdokepConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Idokep: one entry per location."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> IdokepOptionsFlow:
        """Return the options flow."""
        return IdokepOptionsFlow()

    async def _async_check(
        self, user_input: dict[str, Any]
    ) -> tuple[
        str | None,
        dict[str, str],
        dict[str, str],
        list[dict[str, Any]] | None,
        str | None,
        bool,
    ]:
        """Validate the location and find matching map data."""
        try:
            name = await async_validate_location(
                self.hass, user_input[CONF_LOCATION].strip()
            )
        except LocationError as err:
            placeholders = {"shown": err.shown or ""}
            error = "location_fallback" if err.shown else err.error
            return None, {"base": error}, placeholders, None, None, False

        session = async_get_clientsession(self.hass)
        headers = await async_request_headers(self.hass)
        try:
            stations = await FetchSmogStations(
                session,
                user_input[CONF_LOCATION].strip(),
                headers,
            )
        except (aiohttp.ClientError, TimeoutError, StationDataError) as err:
            _LOGGER.warning(
                "Unable to check Időkép smog stations for %r: %s", name, err
            )
            stations = None
        try:
            pollen_location = await FetchPollenLocation(
                session, user_input[CONF_LOCATION].strip(), headers
            )
            pollen_lookup_failed = False
        except (aiohttp.ClientError, TimeoutError, StationDataError) as err:
            _LOGGER.warning(
                "Unable to check Időkép pollen data for %r: %s",
                name,
                err,
            )
            pollen_location = None
            pollen_lookup_failed = True
        return (
            name,
            {},
            {},
            stations,
            pollen_location["city"] if pollen_location else None,
            pollen_lookup_failed,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the kind of Időkép entry to add."""
        return self.async_show_menu(
            step_id="user", menu_options=["location", "station"]
        )

    async def async_step_location(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a weather location."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}
        if user_input is not None:
            (
                name,
                errors,
                placeholders,
                stations,
                pollen_location,
                _,
            ) = await self._async_check(user_input)
            if name is not None:
                await self.async_set_unique_id(entry_unique_id(name))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_LOCATION: name,
                        CONF_SMOG_STATIONS: stations or [],
                        CONF_POLLEN_LOCATION: pollen_location,
                    },
                )

        return self.async_show_form(
            step_id="location",
            data_schema=_schema((user_input or {}).get(CONF_LOCATION)),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the location of an existing entry."""
        entry = self._get_reconfigure_entry()
        if entry.data.get(CONF_STATION_CONFIG_ENTRY):
            return self.async_abort(reason="not_supported")
        old_location: str = entry.data[CONF_LOCATION]
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        if user_input is not None:
            (
                name,
                errors,
                placeholders,
                stations,
                pollen_location,
                pollen_lookup_failed,
            ) = await self._async_check(user_input)
            if name is not None:
                new_unique_id = entry_unique_id(name)
                if new_unique_id != entry.unique_id:
                    await self.async_set_unique_id(new_unique_id)
                    self._abort_if_unique_id_configured()
                self._move_weather_entity(entry.entry_id, old_location, name)
                if stations is None:
                    stations = (
                        entry.data.get(CONF_SMOG_STATIONS, [])
                        if new_unique_id == entry.unique_id
                        else []
                    )
                if pollen_lookup_failed and new_unique_id == entry.unique_id:
                    pollen_location = entry.data.get(CONF_POLLEN_LOCATION)
                options = entry.options
                if new_unique_id != entry.unique_id:
                    options = {
                        **entry.options,
                        CONF_SMOG_SENSORS_ENABLED: False,
                        CONF_POLLEN_SENSORS_ENABLED: False,
                    }
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=new_unique_id,
                    title=name if entry.title == old_location else entry.title,
                    data_updates={
                        CONF_LOCATION: name,
                        CONF_SMOG_STATIONS: stations,
                        CONF_POLLEN_LOCATION: pollen_location,
                    },
                    options=options,
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the forecast length or station refresh interval."""
        if self.config_entry.data.get(CONF_STATION_CONFIG_ENTRY):
            return await self.async_step_station(user_input)
        if user_input is not None:
            options = {CONF_FORECAST_DAYS: int(user_input[CONF_FORECAST_DAYS])}
            if self.config_entry.data.get(CONF_SMOG_STATIONS):
                options[CONF_SMOG_SENSORS_ENABLED] = user_input[
                    CONF_SMOG_SENSORS_ENABLED
                ]
            if self.config_entry.data.get(CONF_POLLEN_LOCATION):
                options[CONF_POLLEN_SENSORS_ENABLED] = user_input[
                    CONF_POLLEN_SENSORS_ENABLED
                ]
            return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=self._options_schema(),
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the refresh interval for one map station."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_STATION_UPDATE_INTERVAL: int(
                        user_input[CONF_STATION_UPDATE_INTERVAL]
                    )
                }
            )

        interval = self.config_entry.options.get(
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
        current = self.config_entry.options.get(
            CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS
        )
        if user_input is not None:
            current = int(user_input.get(CONF_FORECAST_DAYS, current))
        options = self.config_entry.options
        smog_enabled = options.get(CONF_SMOG_SENSORS_ENABLED, False)
        pollen_enabled = options.get(CONF_POLLEN_SENSORS_ENABLED, False)
        if user_input is not None:
            smog_enabled = user_input.get(CONF_SMOG_SENSORS_ENABLED, smog_enabled)
            pollen_enabled = user_input.get(CONF_POLLEN_SENSORS_ENABLED, pollen_enabled)

        schema = {
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
        if self.config_entry.data.get(CONF_SMOG_STATIONS):
            schema[vol.Required(CONF_SMOG_SENSORS_ENABLED, default=smog_enabled)] = (
                BooleanSelector()
            )
        if self.config_entry.data.get(CONF_POLLEN_LOCATION):
            schema[
                vol.Required(CONF_POLLEN_SENSORS_ENABLED, default=pollen_enabled)
            ] = BooleanSelector()
        return vol.Schema(schema)
