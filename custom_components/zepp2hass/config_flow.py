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

from .const import DOMAIN, DEFAULT_DEVICE_NAME, CONF_BASE_URL

# Schema for user input form
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME, default=DEFAULT_DEVICE_NAME): str,
})

# Advanced options schema
ADVANCED_SCHEMA = vol.Schema({
    vol.Optional(CONF_BASE_URL, default=""): str,
})


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

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._device_name: str | None = None

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
            self._device_name = user_input[CONF_NAME]
            # Set unique ID based on device name to prevent duplicates
            await self.async_set_unique_id(self._device_name.lower().strip())
            self._abort_if_unique_id_configured()

            # Move to advanced options step
            return await self.async_step_advanced()

        # Show configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_advanced(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the advanced options step.

        Args:
            user_input: Form data if submitted, None if first display

        Returns:
            Config flow result (form or created entry)
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Generate a secure random webhook ID
            webhook_id = webhook_generate_id()

            # Create entry with provided name, webhook ID, and optional base URL
            return self.async_create_entry(
                title=self._device_name,
                data={
                    CONF_NAME: self._device_name,
                    CONF_WEBHOOK_ID: webhook_id,
                    CONF_BASE_URL: user_input.get(CONF_BASE_URL, ""),
                },
            )

        # Show advanced options form
        return self.async_show_form(
            step_id="advanced",
            data_schema=ADVANCED_SCHEMA,
            errors=errors,
        )
