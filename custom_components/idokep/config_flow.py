"""Config flow for Idokep Weather """

from __future__ import annotations

import voluptuous as vol

import requests

import logging

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
    ATTR_UID,
)

_LOGGER = logging.getLogger(__name__)

class IdokepConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Idokep."""

    VERSION = CONFIG_FLOW_VERSION

    #--------------------- This is required only if options used ---------------
    # @staticmethod
    # @callback 
    # def async_get_options_flow(config_entry: ConfigEntry,) -> IdokepOptionsFlow:
    #     """Create the options flow."""
    #     return IdokepOptionsFlow()
    #---------------------------------------------------------------------------

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        description_placeholders = {}

        _LOGGER.debug("SetUp Flow initiated:")

        if user_input is not None:
            location = user_input[ATTR_API_LOCATION]

            await self.async_set_unique_id(f"{ATTR_UID}")
            self._abort_if_unique_id_configured()

            #--------------------- Location validation disbaled ------------------------
            #errors = _validate_location(location)
            #---------------------------------------------------------------------------

            #--------------------- This is required only if options used ---------------
            # if not errors:
            #     data, options = build_data_and_options(user_input)
            #     return self.async_create_entry(
            #         title=user_input[CONF_NAME], data=data, options=options
            #     )
            #---------------------------------------------------------------------------

            if not errors:
                _LOGGER.debug("Step before entry creation " + str(user_input[CONF_NAME]) + "    " +str(user_input[ATTR_API_LOCATION]))
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data={CONF_NAME: user_input[CONF_NAME], ATTR_API_LOCATION:user_input[ATTR_API_LOCATION]},)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(ATTR_API_LOCATION): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )
    
    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        _LOGGER.debug("Reconfiguration called")
        if user_input is not None:
            # TODO: process user input
            await self.async_set_unique_id(f"{ATTR_UID}")
            self._abort_if_unique_id_mismatch()
            data, options = build_data_and_options(user_input)
            _LOGGER.debug("Reconfiguration DATA:" + str(data))
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates=data,
            )
        
        self.reconfig_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        _LOGGER.debug("Location attribute before reconfiguration: " + str(self.reconfig_entry.data.get(ATTR_API_LOCATION)))

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({vol.Required(ATTR_API_LOCATION,default=self.reconfig_entry.data.get(ATTR_API_LOCATION),): vol.Coerce(str),})
        )

class IdokepOptionsFlow(OptionsFlow):
    """Handle options."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self._conf_app_id: str | None = None

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self._get_options_schema(),
        )

    async def async_end(self):
        """Finalization of the ConfigEntry creation"""
        _LOGGER.info("Recreating entry %s due to configuration change", self.config_entry.entry_id,)
        self.hass.config_entries.async_update_entry(self.config_entry, data=self._infos)
        return self.async_create_entry(title=None, data=None)

    def _get_options_schema(self):
        return vol.Schema(
            {
                vol.Required(
                    ATTR_API_LOCATION,
                    default=self.config_entry.options.get(
                        ATTR_API_LOCATION,
                        self.config_entry.data.get(ATTR_API_LOCATION, DEFAULT_LOCATION),
                    ),
                ): vol.Coerce(str),
            }
        )
    