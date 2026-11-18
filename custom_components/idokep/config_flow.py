"""Config flow for Idokep Weather."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import (
    ATTR_API_LOCATION,
    ATTR_UID,
    CONFIG_FLOW_VERSION,
    DEFAULT_NAME,
    DOMAIN,
)


class IdokepConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Idokep."""

    VERSION = CONFIG_FLOW_VERSION

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            await self.async_set_unique_id(ATTR_UID)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    ATTR_API_LOCATION: user_input[ATTR_API_LOCATION],
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(ATTR_API_LOCATION): str,
                }
            ),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the location of an existing entry."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            await self.async_set_unique_id(ATTR_UID)
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                entry,
                data_updates={ATTR_API_LOCATION: user_input[ATTR_API_LOCATION]},
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        ATTR_API_LOCATION,
                        default=entry.data.get(ATTR_API_LOCATION),
                    ): vol.Coerce(str),
                }
            ),
        )
