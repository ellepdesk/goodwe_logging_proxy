"""Goodwe Inverter Logging Proxy component"""
import logging

from logging_proxy import LoggingProxy
from goodwedecoder import decode

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Goodwe components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    name = entry.title
    serial = entry.data[CONF_SERIAL]

    # Create update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=name,
    )
    proxy = LoggingProxy()
    proxy.add_parser("https://www.goodwe-power.com/Acceptor/Datalog", coordinator.async_set_updated_data)
    device_info = DeviceInfo(
        configuration_url="https://www.semsportal.com",
        identifiers={(DOMAIN, serial)},
        name=entry.title,
        manufacturer="GoodWe",
        model="test",
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        KEY_PROXY: logging_proxy,
        KEY_COORDINATOR: coordinator,
        KEY_DEVICE_INFO: device_info,
    }

    entry.async_on_unload(entry.add_update_listener(update_listener))
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
