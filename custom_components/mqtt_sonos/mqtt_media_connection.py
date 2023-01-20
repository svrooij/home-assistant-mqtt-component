"""Capturing connectiong to mqtt."""
from __future__ import annotations

import json
import logging

from typing import Any

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
import homeassistant.helpers.device_registry as dr

from .const import (
    ATTR_AVAILABILITY_TOPIC,
    ATTR_COMMAND_TOPIC,
    ATTR_DEVICE,
    ATTR_DEVICE_IDENTIFIERS,
    ATTR_DEVICE_MANUFACTURER,
    ATTR_DEVICE_MODEL,
    ATTR_DEVICE_SW_VERSION,
    ATTR_NAME,
    ATTR_STATE_TOPIC,
    ATTR_UNIQUE_ID,
    DISCOVERY_PAYLOAD,
    DOMAIN,
    SOURCE_LINEIN,
    SOURCE_QUEUE,
    SOURCE_TV,
)

_LOGGER = logging.getLogger(__name__)


class MqttMediaConnection:
    """MQTT media connection containing the subscription data."""

    hass: HomeAssistant
    _device_info: DeviceInfo | None
    _config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, data: DISCOVERY_PAYLOAD
    ) -> None:
        """Initialize the MQTT connection data from discovery message."""
        self.hass = hass
        self.state_topic = data[ATTR_STATE_TOPIC]
        self.command_topic = data[ATTR_COMMAND_TOPIC]

        self.availability_topic = data[ATTR_AVAILABILITY_TOPIC]
        self.name = data[ATTR_NAME]
        self._config_entry = config_entry
        if ATTR_DEVICE in data:
            device = data[ATTR_DEVICE]
            self.identifier = device[ATTR_DEVICE_IDENTIFIERS][0]
            self._device_info = DeviceInfo(
                identifiers={(DOMAIN, self.identifier)},
                name=self.name,
                model=device[ATTR_DEVICE_MODEL].replace("Sonos ", ""),
                manufacturer=device[ATTR_DEVICE_MANUFACTURER],
                sw_version=device[ATTR_DEVICE_SW_VERSION],
                connections={
                    # (dr.CONNECTION_NETWORK_MAC, mac),
                    (dr.CONNECTION_UPNP, f"uuid:{self.identifier}"),
                },
            )
        else:
            self.identifier = data[ATTR_UNIQUE_ID]

    @property
    def config_entry(self) -> ConfigEntry:
        """Return parent config entry."""
        return self._config_entry

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return generated device info."""
        return self._device_info

    @property
    def source_list(self) -> list[str]:
        """Generate the allowed sources for this device."""
        if self._device_info is not None:
            if self._device_info["model"] == "Sonos Play:5":
                return [SOURCE_QUEUE, SOURCE_LINEIN]
            if self._device_info["model"] == "Sonos Playbar":
                return [SOURCE_QUEUE, SOURCE_TV]
        return [SOURCE_QUEUE]

    async def send_command(self, command: str, value: Any | None = None) -> None:
        """Send a command, and optional payload to the mqtt server."""
        _LOGGER.debug("Sending command %s to %s", command, self.command_topic)
        payload = json.dumps({"command": command, "input": value})
        await mqtt.async_publish(self.hass, self.command_topic, payload, 0)
