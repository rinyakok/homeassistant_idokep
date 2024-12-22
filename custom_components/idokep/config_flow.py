"""Config flow for Idokep Weather """

from __future__ import annotations

import voluptuous as vol

import requests

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .__init__ import build_data_and_options

from .const import (
    CONFIG_FLOW_VERSION,
    DEFAULT_NAME,
    DEFAULT_LOCATION,
    DOMAIN,
    ATTR_API_LOCATION,
)

class IdokepConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Idokep."""

    VERSION = CONFIG_FLOW_VERSION

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry,) -> IdokepOptionsFlow:
        """Get the options flow for this handler."""
        return IdokepOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        description_placeholders = {}

        if user_input is not None:
            location = user_input[ATTR_API_LOCATION]

            await self.async_set_unique_id(f"{location}")
            self._abort_if_unique_id_configured()

            #Location validation disbaled
            #errors = _validate_location(location)

            if not errors:
                data, options = build_data_and_options(user_input)
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=data, options=options
                )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(ATTR_API_LOCATION): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )


class IdokepOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    def _get_options_schema(self):
        return vol.Schema(
            {
                vol.Required(
                    ATTR_API_LOCATION,
                    default=self.config_entry.options.get(
                        ATTR_API_LOCATION,
                        self.config_entry.data.get(ATTR_API_LOCATION, DEFAULT_LOCATION),
                    ),
                ): vol.In(DEFAULT_LOCATION),
            }
        )