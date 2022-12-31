"""Config flow for Sonos over mqtt integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.config_entry_flow import DiscoveryFlowHandler
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("mqtt_prefix"): str,
    }
)


# class PlaceholderHub:
#     """Placeholder class to make tests pass.

#     TO Remove this placeholder class and replace with things from your PyPI package.
#     """

#     def __init__(self, mqtt_prefix: str) -> None:
#         """Initialize."""
#         self.mqtt_prefix = mqtt_prefix

#     async def authenticate(self, username: str, password: str) -> bool:
#         """Test if we can authenticate with the host."""
#         return True


# async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
#     """Validate the user input allows us to connect.

#     Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
#     """
#     # TD validate the data can be used to set up a connection.

#     # If your PyPI package is not built with async, pass your methods
#     # to the executor:
#     # await hass.async_add_executor_job(
#     #     your_validate_func, data["username"], data["password"]
#     # )

#     hub = PlaceholderHub(data["mqtt_prefix"])

#     # if not await hub.authenticate(data["username"], data["password"]):
#     #     raise InvalidAuth

#     # If you cannot connect:
#     # throw CannotConnect
#     # If the authentication is wrong:
#     # InvalidAuth

#     # Return info that you want to store in the config entry.
#     return {"mqtt_prefix": data["mqtt_prefix"]}


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if Sonos devices have been seen by mqtt."""
    return True


class Sonos2MqttConfigFlow(DiscoveryFlowHandler, domain=DOMAIN):
    """Handle a config flow for Sonos over mqtt."""

    VERSION = 1

    def __init__(self) -> None:
        """Init discovery flow."""
        super().__init__(DOMAIN, "Sonos2mqtt", _async_has_devices)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        # errors = {}

        return self.async_create_entry(title="Instance", data=user_input)

        # try:
        #     info = await validate_input(self.hass, user_input)
        # # except CannotConnect:
        # #     errors["base"] = "cannot_connect"
        # # except InvalidAuth:
        # #     errors["base"] = "invalid_auth"
        # except Exception:  # pylint: disable=broad-except
        #     _LOGGER.exception("Unexpected exception")
        #     errors["base"] = "unknown"
        # else:
        #     return self.async_create_entry(title="Instance", data=user_input)

        # return self.async_show_form(
        #     step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        # )

    async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> FlowResult:
        """Handle mqtt auto discovery."""
        # Triggered if this component is installed and it finds mqtt messages described in the manifest
        if self._async_current_entries() or self._async_in_progress():
            return self.async_abort(reason="single_instance_allowed")
        await self.async_set_unique_id(DOMAIN)
        return self.async_create_entry(title="Instance", data={})


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
