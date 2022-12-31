"""Additional switches for speakers."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_CROSSFADE, DOMAIN, MQTT_PAYLOAD
from .mqtt_media_connection import MqttMediaConnection
from .sonos_manager import SonosManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entries: AddEntitiesCallback,
) -> None:
    """Configure all found entities as switch."""
    _LOGGER.debug("async_setup_entry called")
    manager: SonosManager = hass.data[DOMAIN][config_entry.entry_id]
    connections = manager.get_connections()
    entities = []
    for _, conn in connections.items():
        entities.append(CrossfadeSwitchEntity(conn, hass))
    async_add_entries(entities, True)


class CrossfadeSwitchEntity(SwitchEntity):
    """Crossfade switch for speakers."""

    def __init__(self, conn: MqttMediaConnection, hass: HomeAssistant) -> None:
        """Initialize the crossfade switch entity."""
        self.hass = hass
        self._conn = conn
        self._attr_should_poll = False
        self._attr_name = conn.name + " crossfade"
        self._attr_unique_id = conn.identifier + "_crossfade"
        self._attr_device_info = conn.device_info
        self._attr_available = False

    async def async_added_to_hass(self) -> None:
        """Configure entity once added to hass."""

        @callback
        def message_received(msg: ReceiveMessage) -> None:
            """Handle update from mqtt."""
            try:
                data = MQTT_PAYLOAD(msg.payload)
            except vol.MultipleInvalid as error:
                _LOGGER.warning(
                    "Skipping update because of malformatted data: %s", error
                )
                return
            _LOGGER.debug("Got update from mqtt %s", data)
            self._handle_device_update(data)

        await mqtt.async_subscribe(self.hass, self._conn.state_topic, message_received)

    def _handle_device_update(self, data) -> None:
        """Handle update from mqtt."""
        old_state = self._attr_is_on
        self._attr_is_on = ATTR_CROSSFADE in data and data[ATTR_CROSSFADE] == "On"
        if old_state != self._attr_state or not self._attr_available:
            self._attr_available = True
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Send turn crossfade on to mqtt."""
        return await self._conn.send_command("crossfade", "On")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Send turn crossfade off to mqtt."""
        return await self._conn.send_command("crossfade", "Off")
