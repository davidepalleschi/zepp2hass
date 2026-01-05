"""Config flow for Zepp2Hass integration.

Handles the UI configuration flow when adding a new Zepp device.
Users only need to provide a device name to create an entry.
Advanced options (like custom webhook URL) can be configured later via Options.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.webhook import async_generate_id as webhook_generate_id
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlowWithReload
from homeassistant.const import CONF_NAME, CONF_WEBHOOK_ID

from .const import DOMAIN, DEFAULT_DEVICE_NAME, CONF_BASE_URL

# Schema for user input form
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME, default=DEFAULT_DEVICE_NAME): str,
})

# Schema for options
OPTIONS_SCHEMA = vol.Schema({
    vol.Optional(CONF_BASE_URL, default=""): str,
})


class Zepp2HassConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zepp2Hass.

    This is a simple single-step flow that:
    1. Prompts user for a device name
    2. Generates a secure random webhook ID
    3. Creates a config entry with name and webhook ID

    Advanced options (like custom webhook URL) can be configured later
    via the Options menu.

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

            # Create entry with provided name and webhook ID
            # Custom base URL can be set later via Options
            return self.async_create_entry(
                title=device_name,
                data={
                    CONF_NAME: device_name,
                    CONF_WEBHOOK_ID: webhook_id,
                },
                options={
                    CONF_BASE_URL: "",
                },
            )

        # Show configuration form
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowWithReload:
        """Get the options flow for this handler.

        Args:
            config_entry: The config entry to get options for

        Returns:
            OptionsFlow handler
        """
        return Zepp2HassOptionsFlow(config_entry)


class Zepp2HassOptionsFlow(OptionsFlowWithReload):
    """Handle options flow for Zepp2Hass.

    Allows users to configure advanced options like custom webhook URL
    after the initial setup. Automatically reloads the integration when
    options change.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options.

        Args:
            user_input: Form data if submitted, None if first display

        Returns:
            Config flow result (form or created entry)
        """
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
