"""Constants for the Sonos over mqtt integration."""
from __future__ import annotations

import json

import voluptuous as vol

from homeassistant.components.media_player import MediaPlayerEntityFeature
import homeassistant.helpers.config_validation as cv

DOMAIN = "mqtt_sonos"

ATTR_AVAILABILITY_TOPIC = "availability_topic"
ATTR_COMMAND_TOPIC = "command_topic"
ATTR_DEVICE = "device"
ATTR_DEVICE_CLASS = "device_class"
ATTR_ICON = "icon"
ATTR_NAME = "name"
ATTR_STATE_TOPIC = "state_topic"
ATTR_UNIQUE_ID = "unique_id"

ATTR_DEVICE_IDENTIFIERS = "identifiers"
ATTR_DEVICE_MANUFACTURER = "manufacturer"
ATTR_DEVICE_MODEL = "model"
ATTR_DEVICE_SW_VERSION = "sw_version"

ATTR_COORDINATOR = "coordinatorUuid"
ATTR_CROSSFADE = "crossfade"
ATTR_CURRENT_TRACK = "currentTrack"
ATTR_ENQUEUED_METADATA = "enqueuedMetadata"
ATTR_MUTE = "mute"
ATTR_TITLE = "title"
ATTR_TRANSPORTSTATE = "transportState"
ATTR_UPNP_CLASS = "upnpClass"
ATTR_UUID = "uuid"
ATTR_VOLUME = "volume"

ATTR_POSITION = "position"
ATTR_POSITION_LAST_UPDATE = "lastUpdate"

ATTR_CHANNEL_MASTER = "Master"

ATTR_TRACK_ALBUM_ART_URI = "albumArtUri"
ATTR_TRACK_ARTIST = "artist"
ATTR_TRACK_URI = "trackUri"


DISCOVERY_PAYLOAD = vol.Schema(
    vol.All(
        json.loads,
        vol.Schema(
            {
                vol.Required(ATTR_NAME): cv.string,
                vol.Required(ATTR_STATE_TOPIC): cv.string,
                vol.Required(ATTR_COMMAND_TOPIC): cv.string,
                vol.Required(ATTR_UNIQUE_ID): cv.string,
                vol.Optional(ATTR_DEVICE_CLASS): cv.string,
                vol.Optional(ATTR_ICON): cv.string,
                vol.Optional(ATTR_AVAILABILITY_TOPIC): cv.string,
                vol.Optional(ATTR_DEVICE): vol.Schema(
                    {
                        # vol.Required(ATTR_DEVICE_IDENTIFIERS): # is array??
                        vol.Required(ATTR_DEVICE_MANUFACTURER): cv.string,
                        vol.Required(ATTR_DEVICE_MODEL): cv.string,
                        vol.Optional(ATTR_DEVICE_SW_VERSION): cv.string,
                    },
                    extra=vol.ALLOW_EXTRA,
                ),
            },
            extra=vol.ALLOW_EXTRA,
        ),
    )
)

MQTT_PAYLOAD = vol.Schema(
    vol.All(
        json.loads,
        vol.Schema(
            {
                vol.Required(ATTR_UUID): cv.string,
                vol.Required(ATTR_NAME): cv.string,
                vol.Required(ATTR_TRANSPORTSTATE): cv.string,
                vol.Optional(ATTR_MUTE): vol.Schema(
                    {vol.Required(ATTR_CHANNEL_MASTER): cv.boolean},
                    extra=vol.ALLOW_EXTRA,
                ),
                vol.Optional(ATTR_VOLUME): vol.Schema(
                    {vol.Required(ATTR_CHANNEL_MASTER): cv.positive_int},
                    extra=vol.ALLOW_EXTRA,
                ),
                vol.Optional(ATTR_CURRENT_TRACK): vol.Schema(
                    {
                        vol.Required(ATTR_TITLE): cv.string,
                        vol.Optional(ATTR_TRACK_URI): cv.string,
                        vol.Optional(ATTR_TRACK_ARTIST): cv.string,
                        vol.Optional(ATTR_TRACK_ALBUM_ART_URI): cv.url,
                        vol.Optional(ATTR_UPNP_CLASS): cv.string,
                    },
                    extra=vol.ALLOW_EXTRA,
                ),
                vol.Optional(ATTR_ENQUEUED_METADATA): vol.Schema(
                    {
                        vol.Required(ATTR_TITLE): cv.string,
                        vol.Optional(ATTR_UPNP_CLASS): cv.string,
                    },
                    extra=vol.ALLOW_EXTRA,
                ),
                vol.Optional(ATTR_POSITION): vol.Schema(
                    {
                        vol.Required(ATTR_POSITION): cv.string,  # validate time string?
                        vol.Required(ATTR_POSITION_LAST_UPDATE): cv.positive_int,
                    }
                ),
                vol.Optional(ATTR_CROSSFADE): cv.string,
            },
            extra=vol.ALLOW_EXTRA,
        ),
    )
)

DEFAULT_SPEAKER_FEATURES = (
    MediaPlayerEntityFeature.BROWSE_MEDIA
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

SOURCE_APP = "3rd Party"
SOURCE_QUEUE = "Queue"
SOURCE_LINEIN = "Line-in"
SOURCE_TV = "TV"
