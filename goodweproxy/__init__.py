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


class GoodweProxyCoordinator(DataUpdateCoordinator):
    def __init__(self,  *args, serial_number, **kwargs,):
        super().__init__(*args, **kwargs)
        self.serial_number = serial_number
        proxy = LoggingProxy()
        proxy.add_parser("https://www.goodwe-power.com/Acceptor/Datalog", self.goodwe_decode)

        self.runner = web.AppRunner(proxy)

    async def setup(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, port=8180)
        await site.start()

    def goodwe_decode(self, event):
        data = decode(event['data'])
        if data.pop('device_id') == self.serial_number:
            self.async_set_updated_data(data)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Goodwe components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    name = config_entry.title
    serial = config_entry.data[CONF_SERIAL]
    model = f"GW{serial[1:5]}-{serial[5:7]}"
    # Create update coordinator
    coordinator = GoodweProxyCoordinator(
        hass,
        _LOGGER,
        name=name,
        serial_number=serial
    )

    await coordinator.setup()

    device_info = DeviceInfo(
        configuration_url="https://www.semsportal.com",
        identifiers={(DOMAIN, serial)},
        name=config_entry.title,
        manufacturer="GoodWe",
        model=model,
    )

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))
    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)

    hass.data[DOMAIN][config_entry.entry_id] = {
        KEY_COORDINATOR: coordinator,
        KEY_DEVICE_INFO: device_info,
    }
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    hass.data[DOMAIN][config_entry.entry_id][KEY_COORDINATOR].runner.cleanup()

    if unload_ok:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
