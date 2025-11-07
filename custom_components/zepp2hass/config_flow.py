"""Config flow for Zepp2Hass."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from .const import DOMAIN


class Zepp2HassConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zepp2Hass."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Create entry with device name
            return self.async_create_entry(
                title=user_input[CONF_NAME], data={CONF_NAME: user_input[CONF_NAME]}
            )

        data_schema = vol.Schema({vol.Required(CONF_NAME, default="zepp_device"): str})
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
