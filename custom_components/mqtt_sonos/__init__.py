"""The Sonos over mqtt integration."""
from __future__ import annotations

import logging


from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .sonos_manager import SonosManager

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]  # Platform.SWITCH

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Async setup entry is called if user adds this integration."""

    _LOGGER.debug("async_setup_entry called")

    hass.data.setdefault(DOMAIN, {})
    manager = SonosManager(entry, hass)
    # We start discovery here so it's ready when the components are added.
    await manager.async_start_discovery()
    # The initiated manager is added to hass, to be used in the actual entities
    hass.data[DOMAIN][entry.entry_id] = manager

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    _LOGGER.debug("async_unload_entry called")

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
