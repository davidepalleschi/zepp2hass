"""Config flow for Zepp2Hass integration.

Handles the UI configuration flow when adding a new Zepp device.
Users only need to provide a device name to create an entry.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.webhook import async_generate_id as webhook_generate_id
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME, CONF_WEBHOOK_ID

from .const import DOMAIN, DEFAULT_DEVICE_NAME

# Schema for user input form
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME, default=DEFAULT_DEVICE_NAME): str,
})


class Zepp2HassConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zepp2Hass.

    This is a simple single-step flow that:
    1. Prompts user for a device name
    2. Generates a secure random webhook ID
    3. Creates a config entry with name and webhook ID

    The webhook URL uses a random ID for security (not guessable).
    """

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial configuration step.

        Args:
            user_input: Form data if submitted, None if first display

        Returns:
            Config flow result (form or created entry)
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Set unique ID based on device name to prevent duplicates
            await self.async_set_unique_id(user_input[CONF_NAME].lower().strip())
            self._abort_if_unique_id_configured()

            # Generate a secure random webhook ID
            webhook_id = webhook_generate_id()

            # Create entry with provided name and webhook ID
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_WEBHOOK_ID: webhook_id,
                },
            )

        # Show configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
