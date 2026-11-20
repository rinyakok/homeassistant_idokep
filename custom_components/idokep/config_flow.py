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
    CONF_STATION_SENSORS_ENABLED,
    CONFIG_FLOW_VERSION,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_STATION_SENSORS_ENABLED,
    DOMAIN,
    FORECAST_DAYS_CHOICES,
    entry_unique_id,
    weather_unique_id,
)
from .coordinator import BUDAPEST_TZ_NAME, FetchWeatherData, async_request_headers

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
    ) -> tuple[str | None, dict[str, str], dict[str, str]]:
        """Validate the typed location; return (name, errors, placeholders)."""
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
    ) -> ConfigFlowResult:
        """Add a location."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}
        if user_input is not None:
            name, errors, placeholders = await self._async_check(user_input)
            if name is not None:
                await self.async_set_unique_id(entry_unique_id(name))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=name, data={CONF_LOCATION: name})

        return self.async_show_form(
            step_id="user",
            data_schema=_schema((user_input or {}).get(CONF_LOCATION)),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the location of an existing entry."""
        entry = self._get_reconfigure_entry()
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the forecast length and optional station sensors."""
        if user_input is not None:
            station_sensors_enabled = user_input[CONF_STATION_SENSORS_ENABLED]
            measurement_point = (user_input.get(CONF_MEASUREMENT_POINT) or "").strip()
            if station_sensors_enabled and not measurement_point:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._options_schema(user_input),
                    errors={"base": "measurement_point_required"},
                )
            return self.async_create_entry(
                data={
                    CONF_FORECAST_DAYS: int(user_input[CONF_FORECAST_DAYS]),
                    CONF_STATION_SENSORS_ENABLED: station_sensors_enabled,
                    CONF_MEASUREMENT_POINT: measurement_point,
                }
            )

        return self.async_show_form(
            step_id="init",
            data_schema=self._options_schema(),
        )

    def _options_schema(self, user_input: dict[str, Any] | None = None) -> vol.Schema:
        """Build the options form with the saved values as defaults."""
        current = self.config_entry.options.get(
            CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS
        )
        options = self.config_entry.options
        point = options.get(CONF_MEASUREMENT_POINT, "")
        if user_input is not None:
            current = int(user_input.get(CONF_FORECAST_DAYS, current))
            point = user_input.get(CONF_MEASUREMENT_POINT, point)
        enabled = options.get(
            CONF_STATION_SENSORS_ENABLED, DEFAULT_STATION_SENSORS_ENABLED
        )
        if user_input is not None:
            enabled = user_input.get(CONF_STATION_SENSORS_ENABLED, enabled)

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
                vol.Required(
                    CONF_STATION_SENSORS_ENABLED, default=enabled
                ): BooleanSelector(),
                vol.Optional(CONF_MEASUREMENT_POINT, default=point): TextSelector(),
            }
        )
