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
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, DEFAULT_DEVICE_NAME, CONF_BASE_URL


class Zepp2HassConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zepp2Hass.

    This is a simple single-step flow that:
    1. Prompts user for a device name
    2. Optionally shows advanced settings for custom webhook URL
    3. Generates a secure random webhook ID
    4. Creates a config entry with name and webhook ID

    The webhook URL uses a random ID for security (not guessable).
    """

    VERSION = 1
    MINOR_VERSION = 2

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
            device_name = user_input[CONF_NAME]
            # Set unique ID based on device name to prevent duplicates
            await self.async_set_unique_id(device_name.lower().strip())
            self._abort_if_unique_id_configured()

            # Generate a secure random webhook ID
            webhook_id = webhook_generate_id()

            # Create entry with provided name, webhook ID, and optional base URL
            return self.async_create_entry(
                title=device_name,
                data={
                    CONF_NAME: device_name,
                    CONF_WEBHOOK_ID: webhook_id,
                    CONF_BASE_URL: user_input.get(CONF_BASE_URL, ""),
                },
            )

        # Show configuration form with sections
        # Using the new Home Assistant sections format for collapsible advanced options
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors,
        )

    def _get_schema(self) -> vol.Schema:
        """Get the schema for the config form with sections.

        Returns:
            Schema with main section and advanced section
        """
        return vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_DEVICE_NAME): str,
                vol.Optional(
                    CONF_BASE_URL,
                    description={"suggested_value": ""},
                ): str,
            }
        )
