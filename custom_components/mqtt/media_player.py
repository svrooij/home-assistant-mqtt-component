"""Support for MQTT MEdia players."""
from __future__ import annotations

import functools

# from collections.abc import Callable
import json
import logging
import time
from typing import Any

import voluptuous as vol

from homeassistant.components import media_player, media_source
from homeassistant.components.media_player import (  # DEVICE_CLASSES_SCHEMA,; MEDIA_TYPE_MUSIC,; REPEAT_MODE_ONE,
    ATTR_MEDIA_ENQUEUE,
    MediaClass,
    MediaPlayerDeviceClass,
    MediaPlayerEnqueue,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
    async_process_play_media_url,
)
from homeassistant.components.media_player.browse_media import BrowseMedia
from homeassistant.components.media_player.errors import BrowseError
from homeassistant.components.media_source.models import BrowseMediaSource
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt

from . import subscription
from .config import MQTT_RW_SCHEMA
from .const import CONF_COMMAND_TOPIC, CONF_ENCODING, CONF_QOS, CONF_STATE_TOPIC
from .debug_info import log_messages
from .mixins import (  # warn_for_legacy_schema,; async_setup_platform_discovery,; async_setup_platform_helper,
    MQTT_ENTITY_COMMON_SCHEMA,
    MqttEntity,
    async_setup_entry_helper,
)
from .models import ReceiveMessage

# from typing import Any


DEFAULT_NAME = "MQTT Media Player"

PLATFORM_SCHEMA_MODERN = MQTT_RW_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        # vol.Optional(CONF_OPTIMISTIC, default=DEFAULT_OPTIMISTIC): cv.boolean,
        # vol.Optional(CONF_PAYLOAD_OFF, default=DEFAULT_PAYLOAD_OFF): cv.string,
        # vol.Optional(CONF_PAYLOAD_ON, default=DEFAULT_PAYLOAD_ON): cv.string,
        # vol.Optional(CONF_STATE_OFF): cv.string,
        # vol.Optional(CONF_STATE_ON): cv.string,
        # vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
        # vol.Optional(CONF_DEVICE_CLASS): DEVICE_CLASSES_SCHEMA,
    }
).extend(MQTT_ENTITY_COMMON_SCHEMA.schema)

DISCOVERY_SCHEMA = PLATFORM_SCHEMA_MODERN.extend({}, extra=vol.REMOVE_EXTRA)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MQTT media player through configuration.yaml and dynamically through MQTT discovery."""
    # config_entry.async_on_unload(
    #     await async_setup_platform_discovery(
    #         hass, media_player.DOMAIN, PLATFORM_SCHEMA_MODERN
    #     )
    # )
    setup = functools.partial(
        _async_setup_entity, hass, async_add_entities, config_entry=config_entry
    )
    await async_setup_entry_helper(hass, media_player.DOMAIN, setup, DISCOVERY_SCHEMA)


async def _async_setup_entity(
    hass: HomeAssistant,
    async_add_entities: AddEntitiesCallback,
    config: ConfigType,
    config_entry: ConfigEntry,
    discovery_data: DiscoveryInfoType | None = None,
) -> None:
    """Set up the MQTT humidifier."""
    async_add_entities([MqttMediaPlayer(hass, config, config_entry, discovery_data)])


class MqttMediaPlayer(MqttEntity, MediaPlayerEntity):
    """Representation of a media player that can be controlled using MQTT."""

    _entity_id_format = media_player.ENTITY_ID_FORMAT
    _attr_media_content_type = MediaClass.TRACK
    _attr_supported_features = (
        MediaPlayerEntityFeature.BROWSE_MEDIA
        # | MediaPlayerEntityFeature.CLEAR_PLAYLIST
        # | MediaPlayerEntityFeature.GROUPING
        | MediaPlayerEntityFeature.NEXT_TRACK
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PLAY_MEDIA
        | MediaPlayerEntityFeature.PREVIOUS_TRACK
        | MediaPlayerEntityFeature.REPEAT_SET
        | MediaPlayerEntityFeature.SEEK
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SHUFFLE_SET
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
    )
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER

    def __init__(
        self,
        hass: HomeAssistant,
        config: ConfigType,
        config_entry: ConfigEntry,
        discovery_data: DiscoveryInfoType | None,
    ) -> None:
        """Initialize the MQTT media player."""
        # self._state = None

        # self._state_on = None
        # self._state_off = None
        self._optimistic = None

        MqttEntity.__init__(self, hass, config, config_entry, discovery_data)

    @staticmethod
    def config_schema() -> vol.Schema:
        """Return the config schema."""
        return DISCOVERY_SCHEMA

    def _setup_from_config(self, config: ConfigType) -> None:
        """(Re)Setup the entity."""

    def _prepare_subscribe_topics(self) -> None:
        """(Re)Subscribe to topics."""

        @callback
        @log_messages(self.hass, self.entity_id)
        # def state_message_received(msg):
        def state_received(msg: ReceiveMessage) -> None:
            """Handle new MQTT state messages."""
            payload = json.loads(msg.payload)
            sonos_state = payload.get("transportState")
            if sonos_state in ("PAUSED_PLAYBACK", "STOPPED"):
                self._attr_state = MediaPlayerState.PAUSED
            else:
                self._attr_state = MediaPlayerState.PLAYING

            current_track = payload.get("currentTrack", {})
            self._attr_media_content_type = MediaClass.TRACK
            self._attr_media_content_id = current_track.get("trackUri")
            self._attr_media_artist = current_track.get("artist")
            self._attr_media_title = current_track.get("title")
            self._attr_media_image_url = current_track.get("albumArtUri")
            self._attr_media_duration = time_string_to_seconds(
                current_track.get("duration")
            )

            members = payload.get("members")
            if members is not None:
                self._attr_group_members = []
                for member in members:
                    self._attr_group_members.append(member.get("name"))
            else:
                self._attr_group_members = None

            volume = payload.get("volume", {}).get("Master")
            if volume is not None:
                self._attr_volume_level = volume / 100

            self._attr_is_volume_muted = payload.get("mute", {}).get("Master")
            self._attr_shuffle = payload.get("shuffle")
            self._attr_media_playlist = payload.get("enqueuedMetadata", {}).get("title")
            self._attr_available = True

            position = payload.get("position")
            if position is not None:
                self._attr_media_position = time_string_to_seconds(
                    position.get("position")
                )
                update = position.get("lastUpdate")
                if update is not None:
                    self._attr_media_position_updated_at = update
                else:
                    # Not really sure about this fallback, maybe empty it? (suggestions?)
                    self._attr_media_position_updated_at = dt.utcnow()

            self.async_write_ha_state()

        self._sub_state = subscription.async_prepare_subscribe_topics(
            self.hass,
            self._sub_state,
            {
                CONF_STATE_TOPIC: {
                    "topic": self._config.get(CONF_STATE_TOPIC),
                    "msg_callback": state_received,
                    "qos": self._config[CONF_QOS],
                    "encoding": self._config[CONF_ENCODING] or None,
                }
            },
        )

    async def _subscribe_topics(self) -> None:
        """(Re)Subscribe to topics."""
        await subscription.async_subscribe_topics(self.hass, self._sub_state)

    async def send_command(self, command: str, value: Any | None = None) -> None:
        """Send a command, and optional payload to the mqtt server."""
        payload = json.dumps({"command": command, "input": value})
        await self.async_publish(
            self._config[CONF_COMMAND_TOPIC],
            payload,
        )

    async def async_media_play(self) -> None:
        """Send play command to mqtt."""
        await self.send_command("play")
        self._attr_state = MediaPlayerState.BUFFERING
        self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        """Send pause command to mqtt."""
        await self.send_command("pause")
        self._attr_state = MediaPlayerState.PAUSED
        self.async_write_ha_state()

    async def async_media_play_pause(self) -> None:
        """Send toggle command to mqtt."""
        await self.send_command("toggle")

    async def async_media_next_track(self) -> None:
        """Send next command to mqtt."""
        await self.send_command("next")

    async def async_media_previous_track(self) -> None:
        """Send previous command to mqtt."""
        await self.send_command("previous")

    async def async_mute_volume(self, mute: bool) -> None:
        """Send mute command to mqtt."""
        await self.send_command("mute", mute)
        self._attr_is_volume_muted = mute
        self.async_write_ha_state()

    async def async_set_volume_level(self, volume: float) -> None:
        """Send volume and unmute command to mqtt."""
        await self.send_command("volume", volume * 100)
        self._attr_volume_level = volume
        if self._attr_is_volume_muted is True:
            await self.send_command("unmute")
            self._attr_is_volume_muted = False
        self.async_write_ha_state()

    async def async_media_seek(self, position: float) -> None:
        """Send seek command to mqtt."""
        await self.send_command("seek", seconds_to_time_string(position))
        # self._attr_media_position = position
        # self._attr_media_position_updated_at = dt.utcnow()
        # self.async_write_ha_state()

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        """Send repeat mode to mqtt."""
        if repeat == RepeatMode.ALL:
            await self.send_command("repeat", True)
        elif repeat == RepeatMode.OFF:
            await self.send_command("repeat", False)
        # how about 'one'?
        # await self.send_command("repeat", repeat)
        self._attr_repeat = repeat
        self.async_write_ha_state()

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Send shuffle to mqtt."""
        await self.send_command("shuffle", shuffle)
        self._attr_shuffle = shuffle
        self.async_write_ha_state()

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""

        # Media_content_id is empty, create root
        if media_content_id is None:
            return await media_root_payload(self.hass)

        if media_source.is_media_source_id(media_content_id):
            return await media_source.async_browse_media(
                self.hass, media_content_id, content_filter=media_source_filter
            )
        raise BrowseError(f"Media not found: {media_content_type} / {media_content_id}")

    async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        enqueue: MediaPlayerEnqueue | None = None,
        announce: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Play some media file."""
        # Use 'replace' as the default enqueue option
        enqueue = kwargs.get(ATTR_MEDIA_ENQUEUE, MediaPlayerEnqueue.ADD)
        _LOGGER.debug(
            'MQTT Media Player play media: "%s" enqueue: "%s" announce: "%s"',
            media_id,
            enqueue,
            announce,
        )
        if media_id == "sm://notification/ding":
            await self.send_command(
                "notify",
                {
                    "trackUri": "https://cdn.smartersoft-group.com/various/pull-bell-short.mp3",
                    "timeout": 10,
                    "volume": 20,
                    "delayMs": 600,
                },
            )
            return
        if media_source.is_media_source_id(media_id):
            info = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )

            if media_id.startswith("media-source://tts/") or announce is True:
                # How Do I get the absolute URL?
                media_uri = async_process_play_media_url(self.hass, info.url)
                await self.send_command(
                    "notify",
                    {
                        "trackUri": media_uri,
                        "timeout": 20,
                        "volume": 15,
                        "delayMs": 600,
                    },
                )
                return

            if media_id.startswith("media-source://radio_browser/"):
                # Don't know how to play....
                # await self.send_command(
                #     "setavtransporturi", "x-sonosapi-stream:" + info.url
                # )
                # await self.send_command(
                #     "adv-command",
                #     {
                #         "cmd": "AVTransportService.SetAVTransportURI",
                #         "val": {
                #             "InstanceID": 0,
                #             "CurrentURI": info.url,
                #             "CurrentURIMetaData": {
                #                 "UpnpClass": "object.item.audioItem.audioBroadcast",
                #                 "ItemId": "-1",
                #             },
                #         },
                #     },
                # )

                return

            await self.send_command("queue", info.url)
            return

        if media_id.startswith("spotify:"):
            await self.send_command("queue", info.url)
            return
        _LOGGER.error(
            'MQTT media player does not support a media type of "%s"', media_type
        )
        return None
        # return await super().async_play_media(media_type, media_id, **kwargs)


def time_string_to_seconds(time_string: str | None) -> int | None:
    """Convert a time string like 1:02:01 to 3721 seconds."""
    if time_string is None or time_string == "NOT_IMPLEMENTED":
        return None
    return sum(
        x * int(t) for x, t in zip([1, 60, 3600], reversed(time_string.split(":")))
    )


def seconds_to_time_string(seconds: float | None) -> str | None:
    """Convert seconds to time string HH:MM:SS."""
    # Skip values higher then 1 day
    if seconds is None or seconds >= 86400:
        return None

    return time.strftime("%H:%M:%S", time.gmtime(seconds))


async def media_root_payload(
    hass: HomeAssistant,
) -> BrowseMedia | BrowseMediaSource:
    """Create root media browser."""
    children: list[BrowseMedia] = []

    # if "spotify" in hass.config.components:
    #     result = await spotify.async_browse_media(hass, None, None)
    #     children.extend(result.children)

    try:
        # Load default media, but filter for audio only (not sure why it shows "Camera")
        item = await media_source.async_browse_media(
            hass, None, content_filter=media_source_filter
        )

        # If domain is None, it's overview of available sources
        if item.domain is None and item.children is not None:
            children.extend(item.children)
        else:
            children.append(item)
    except media_source.BrowseError:
        pass

    # Add random notification sound
    children.append(
        BrowseMedia(
            title="Ding",
            media_content_type="notification",
            media_class=MediaClass.APP,
            media_content_id="sm://notification/ding",
            thumbnail="https://brands.home-assistant.io/_/sonos/logo.png",
            can_expand=False,
            can_play=True,
        )
    )

    return BrowseMedia(
        title="Sonos",
        media_class=MediaClass.DIRECTORY,
        media_content_id="",
        media_content_type="root",
        can_play=False,
        can_expand=True,
        children=children,
    )


def media_source_filter(item: BrowseMedia) -> bool:
    """Filter media sources."""
    return item.media_content_type.startswith("audio/")
