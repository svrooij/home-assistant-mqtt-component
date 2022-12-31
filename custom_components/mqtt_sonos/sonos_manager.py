"""Sonos manager."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import ATTR_UNIQUE_ID, DISCOVERY_PAYLOAD
from .mqtt_media_connection import MqttMediaConnection

_LOGGER = logging.getLogger(__name__)

DISCOVERY_TOPIC = "sonos2mqtt/discovery/#"


class SonosManager:
    """Sonos manager to manage MQTT subscriptions."""

    _config_entry: ConfigEntry

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Create sonos manager to do the discovery of entities."""
        self._config_entry = config_entry
        self.connections: dict[str, MqttMediaConnection] = {}

    def get_connections(self) -> dict[str, MqttMediaConnection]:
        """Load all discovered speakers."""
        return self.connections

    async def async_start_discovery(self, hass: HomeAssistant) -> None:
        """Start sonos device discovery, call from __init__."""

        @callback
        def discovery_received(msg: ReceiveMessage):
            """MQTT message callback."""
            try:
                data = DISCOVERY_PAYLOAD(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.warning(
                    "Skipping discovery because of malformatted data: %s", error
                )
                return
            _LOGGER.debug("Got sonos discovery data %s", data)
            uuid = data[ATTR_UNIQUE_ID]
            if uuid in self.connections:
                _LOGGER.debug("Skipping discovery update")
            else:
                self.connections[uuid] = MqttMediaConnection(
                    hass, self._config_entry, data
                )

        await mqtt.async_subscribe(hass, DISCOVERY_TOPIC, discovery_received)
