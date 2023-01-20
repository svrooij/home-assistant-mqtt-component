"""Sonos manager."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import Platform
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import ATTR_UNIQUE_ID, DISCOVERY_PAYLOAD, EVENT_DISCOVERED
from .mqtt_media_connection import MqttMediaConnection

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]  # Platform.SWITCH

_LOGGER = logging.getLogger(__name__)

DISCOVERY_TOPIC = "sonos2mqtt/discovery/#"


class SonosManager:
    """Sonos manager to manage MQTT subscriptions."""

    _config_entry: ConfigEntry
    hass: HomeAssistant

    def __init__(self, config_entry: ConfigEntry, hass: HomeAssistant) -> None:
        """Create sonos manager to do the discovery of entities."""
        _LOGGER.debug("__init__ called")
        self._config_entry = config_entry
        self.hass = hass
        self.connections: dict[str, MqttMediaConnection] = {}

    def get_connections(self) -> dict[str, MqttMediaConnection]:
        """Load all discovered speakers."""
        return self.connections

    async def async_start_discovery(self) -> None:
        """Start sonos device discovery, call from __init__."""
        _LOGGER.debug("async_start_discovery called")

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
                _LOGGER.debug("Updating discovery info")
                self.connections[uuid] = MqttMediaConnection(
                    self.hass, self._config_entry, data
                )
                # Not sure if this is needed or what this does
                # async_dispatcher_send(self.hass, EVENT_DISCOVERED, self.connections[uuid])
            else:
                self.connections[uuid] = MqttMediaConnection(
                    self.hass, self._config_entry, data
                )
                async_dispatcher_send(
                    self.hass, EVENT_DISCOVERED, self.connections[uuid]
                )

        await mqtt.async_subscribe(self.hass, DISCOVERY_TOPIC, discovery_received)
