"""The Sonos over mqtt integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .sonos_manager import SonosManager

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]  # Platform.SWITCH


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Async setup entry is called if user adds this integration."""

    hass.data.setdefault(DOMAIN, {})
    manager = SonosManager(entry)
    # We start discovery here so it's ready when the components are added.
    await manager.async_start_discovery(hass)
    # The initiated manager is added to hass, to be used in the actual entities
    hass.data[DOMAIN][entry.entry_id] = manager

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
