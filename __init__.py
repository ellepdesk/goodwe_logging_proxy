"""Goodwe Inverter Logging Proxy component"""
import logging

from .logging_proxy import LoggingProxy
from .goodwedecoder import decode

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from aiohttp import web

from .const import *

_LOGGER = logging.getLogger(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Goodwe components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    name = config_entry.title
    serial = config_entry.data[CONF_SERIAL]

    # Create update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=name,
    )

    def goodwe_decode(event):
        if event['data']['device_id'] == serial:
            coordinator.async_set_updated_data(decode(event['data']))

    proxy = LoggingProxy()
    proxy.add_parser("https://www.goodwe-power.com/Acceptor/Datalog", goodwe_decode)
    device_info = DeviceInfo(
        configuration_url="https://www.semsportal.com",
        identifiers={(DOMAIN, serial)},
        name=config_entry.title,
        manufacturer="GoodWe",
        model="test",
    )

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))
    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    runner = web.AppRunner(proxy)
    await runner.setup()
    site = web.TCPSite(runner, port=8180)
    await site.start()

    hass.data[DOMAIN][config_entry.entry_id] = {
        KEY_PROXY: logging_proxy,
        KEY_COORDINATOR: coordinator,
        KEY_DEVICE_INFO: device_info,
        KEY_RUNNNER: runner,
    }

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    hass.data[DOMAIN][config_entry.entry_id][KEY_RUNNNER].cleanup()

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
