"""Goodwe Inverter Logging Proxy component"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import CONF_PORT

from .goodweplatform import GoodWeProxyCoordinator

from .const import *

_LOGGER = logging.getLogger(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up the Goodwe components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    name = config_entry.title
    serial = config_entry.data[CONF_SERIAL]
    port = config_entry.data[CONF_PORT]
    model = f"GW{serial[1:5]}-{serial[5:7]}"
    # Create update coordinator
    coordinator = GoodWeProxyCoordinator(
        hass,
        _LOGGER,
        name=name,
        serial_number=serial,
        port=8180,
    )

    await coordinator.setup()

    if TYPE_CHECKING:
        assert config_entry.unique_id

    device_info = DeviceInfo(
        configuration_url="https://www.semsportal.com",
        identifiers={(DOMAIN, config_entry.unique_id)},
        name=config_entry.title,
        manufacturer="GoodWe",
        model=model,
    )
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = {
        GOODWE_COORDINATOR: coordinator,
        GOODWE_DEVICE_INFO: device_info,
    }

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data[GOODWE_COORDINATOR].stop()