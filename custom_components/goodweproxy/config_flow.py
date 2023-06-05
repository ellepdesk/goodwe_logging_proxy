from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from homeassistant.const import CONF_PORT
from .const import DOMAIN, DEFAULT_NAME, CONF_SERIAL

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SERIAL): cv.string,
        vol.Optional(CONF_PORT, default=8180): cv.int,
    }
)


class GoodweProxyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            serial = user_input[CONF_SERIAL]
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={
                    CONF_SERIAL: serial,
                    CONF_PORT: port,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
        )
