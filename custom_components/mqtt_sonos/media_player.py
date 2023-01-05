"""MQTT Media player entity."""
from __future__ import annotations

import logging
import time
import datetime as dt
from typing import Any

import voluptuous as vol

from homeassistant.components import media_source, mqtt
from homeassistant.components.media_player import (
    ATTR_MEDIA_ENQUEUE,
    BrowseError,
    BrowseMedia,
    MediaClass,
    MediaPlayerDeviceClass,
    MediaPlayerEnqueue,
    MediaPlayerEntity,
    MediaPlayerState,
    MediaType,
    RepeatMode,
    async_process_play_media_url,
)
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CHANNEL_MASTER,
    ATTR_CURRENT_TRACK,
    ATTR_ENQUEUED_METADATA,
    ATTR_MUTE,
    ATTR_POSITION,
    ATTR_POSITION_LAST_UPDATE,
    ATTR_TITLE,
    ATTR_TRACK_ALBUM,
    ATTR_TRACK_ALBUM_ART_URI,
    ATTR_TRACK_ARTIST,
    ATTR_TRACK_DURATION,
    ATTR_TRACK_URI,
    ATTR_TRANSPORTSTATE,
    ATTR_UPNP_CLASS,
    ATTR_VOLUME,
    DEFAULT_SPEAKER_FEATURES,
    DOMAIN,
    MQTT_PAYLOAD,
    SOURCE_APP,
    SOURCE_LINEIN,
    SOURCE_QUEUE,
    SOURCE_TV,
)
from .mqtt_media_connection import MqttMediaConnection
from .sonos_manager import SonosManager

_LOGGER = logging.getLogger(__name__)

BUILDIN_NOTIFICATION = "sonos2mqtt://bell"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entries: AddEntitiesCallback,
) -> None:
    """Configure all found entities as media_player."""
    _LOGGER.debug("async_setup_entry called")
    manager: SonosManager = hass.data[DOMAIN][config_entry.entry_id]
    connections = manager.get_connections()
    entities = []
    for _, conn in connections.items():
        entities.append(SonosMediaPlayerEntity(conn, hass))
    async_add_entries(entities, True)


class SonosMediaPlayerEntity(MediaPlayerEntity):
    """Representation of a Sonos entity."""

    def __init__(self, conn: MqttMediaConnection, hass: HomeAssistant) -> None:
        """Initialize the media player entity."""
        self.hass = hass
        self._conn = conn
        self._attr_should_poll = False
        self._attr_name = conn.name
        self._attr_unique_id = conn.identifier + "_speaker"
        self._attr_device_class = MediaPlayerDeviceClass.SPEAKER
        self._attr_media_content_type = MediaClass.MUSIC
        self._attr_supported_features = DEFAULT_SPEAKER_FEATURES

        self._attr_device_info = conn.device_info
        self._attr_available = True
        self._attr_source_list = conn.source_list

    async def async_added_to_hass(self) -> None:
        """Automatically called if entity is activated."""

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

    def _handle_device_update(self, data: MQTT_PAYLOAD) -> None:
        """Update data from mqtt message."""
        self._attr_available = True
        state = data[ATTR_TRANSPORTSTATE]
        if state in ("PAUSED_PLAYBACK", "STOPPED"):
            self._attr_state = MediaPlayerState.PAUSED
        else:
            self._attr_state = MediaPlayerState.PLAYING

        if ATTR_CURRENT_TRACK in data:
            track = data[ATTR_CURRENT_TRACK]
            if ATTR_TITLE in track:
                self._attr_media_title = track[ATTR_TITLE]

            if ATTR_TRACK_ALBUM in track:
                self._attr_media_album_name = track[ATTR_TRACK_ALBUM]
            else:
                self._attr_media_album_name = None

            if ATTR_TRACK_ALBUM_ART_URI in track:
                image_url = track[ATTR_TRACK_ALBUM_ART_URI]
                self._attr_media_image_url = image_url
                self._attr_media_image_remotely_accessible = image_url.startswith(
                    "https://"
                )
            if ATTR_TRACK_ARTIST in track:
                self._attr_media_artist = track[ATTR_TRACK_ARTIST]
                self._attr_media_album_artist = track[ATTR_TRACK_ARTIST]
            else:
                self._attr_media_album_artist = ""
                self._attr_media_artist = ""

            if ATTR_TRACK_URI in track:
                track_uri = track[ATTR_TRACK_URI]
                self._attr_media_content_id = track_uri
                if track_uri.startswith("x-rincon-stream:"):
                    self._attr_source = SOURCE_LINEIN
                elif track_uri.startswith("x-sonos-htastream:RINCON_"):
                    self._attr_source = SOURCE_TV
                else:
                    self._attr_source = SOURCE_APP

            if ATTR_TRACK_DURATION in track:
                self._attr_media_duration = time_string_to_seconds(
                    track[ATTR_TRACK_DURATION]
                )
            else:
                self._attr_media_duration = None

        if ATTR_ENQUEUED_METADATA in data:
            meta = data[ATTR_ENQUEUED_METADATA]
            if ATTR_TITLE in meta:
                self._attr_media_playlist = meta[ATTR_TITLE]
            if ATTR_UPNP_CLASS in meta and meta[ATTR_UPNP_CLASS].startswith(
                "object.container.playlistContainer"
            ):
                self._attr_source = SOURCE_QUEUE

        else:
            self._attr_media_playlist = None

        if ATTR_VOLUME in data:
            self._attr_volume_level = data[ATTR_VOLUME][ATTR_CHANNEL_MASTER] / 100

        if ATTR_MUTE in data:
            self._attr_is_volume_muted = data[ATTR_MUTE][ATTR_CHANNEL_MASTER]

        if ATTR_POSITION in data:
            self._attr_media_position = time_string_to_seconds(
                data[ATTR_POSITION][ATTR_POSITION]
            )
            self._attr_media_position_updated_at = dt.datetime.fromtimestamp(
                data[ATTR_POSITION][ATTR_POSITION_LAST_UPDATE] / 1000
            )

        self.async_write_ha_state()

    async def async_media_play(self) -> None:
        """Send play command to mqtt."""
        await self._conn.send_command("play")
        self._attr_state = MediaPlayerState.BUFFERING
        self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        """Send pause command to mqtt."""
        await self._conn.send_command("pause")
        self._attr_state = MediaPlayerState.PAUSED
        self.async_write_ha_state()

    async def async_media_play_pause(self) -> None:
        """Send toggle command to mqtt."""
        await self._conn.send_command("toggle")

    async def async_media_next_track(self) -> None:
        """Send next command to mqtt."""
        await self._conn.send_command("next")

    async def async_media_previous_track(self) -> None:
        """Send previous command to mqtt."""
        await self._conn.send_command("previous")

    async def async_media_seek(self, position: float) -> None:
        """Send seek command to mqtt."""
        await self._conn.send_command("seek", seconds_to_time_string(position))

    async def async_mute_volume(self, mute: bool) -> None:
        """Send mute command to mqtt."""
        await self._conn.send_command("mute", mute)
        self._attr_is_volume_muted = mute
        self.async_write_ha_state()

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        """Send repeat mode to mqtt."""
        if repeat == RepeatMode.ALL:
            await self._conn.send_command("repeat", True)
        elif repeat == RepeatMode.OFF:
            await self._conn.send_command("repeat", False)
        # how about 'one'?
        # await self._conn.send_command("repeat", repeat)
        self._attr_repeat = repeat
        self.async_write_ha_state()

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Send shuffle to mqtt."""
        await self._conn.send_command("shuffle", shuffle)
        self._attr_shuffle = shuffle
        self.async_write_ha_state()

    async def async_set_volume_level(self, volume: float) -> None:
        """Send volume and unmute command to mqtt."""
        await self._conn.send_command("volume", volume * 100)
        self._attr_volume_level = volume
        if self._attr_is_volume_muted is True:
            await self._conn.send_command("unmute")
            self._attr_is_volume_muted = False
        self.async_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        """Send new source to mqtt."""
        if source == SOURCE_LINEIN:
            await self._conn.send_command("switchtoline")
        elif source == SOURCE_TV:
            await self._conn.send_command("switchtotv")
        elif source == SOURCE_QUEUE:
            await self._conn.send_command("switchtoqueue")

    async def async_browse_media(
        self,
        media_content_type: str | None = None,
        media_content_id: str | None = None,
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
        if media_id == BUILDIN_NOTIFICATION:
            await self._conn.send_command(
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

                media_uri = async_process_play_media_url(self.hass, info.url)
                await self._conn.send_command(
                    "notify",
                    {
                        "trackUri": media_uri,
                        "timeout": 30,
                        "volume": 15,
                        "delayMs": 600,
                    },
                )
                return

            if media_id.startswith("media-source://radio_browser/"):
                # Don't know how to play....
                await self._conn.send_command("setavtransporturi", info.url)
                # await self._conn.send_command(
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

            await self._conn.send_command("queue", info.url)
            return

        if media_id.startswith("spotify:"):
            await self._conn.send_command("queue", info.url)
            return
        _LOGGER.error(
            'MQTT media player does not support a media type of "%s"', media_type
        )
        return None


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
) -> BrowseMedia:
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
            title="Ring bell",
            media_content_type=MediaType.URL,
            media_class=MediaClass.APP,
            media_content_id=BUILDIN_NOTIFICATION,
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
