"""Goodwe Inverter Logging Proxy component"""
from __future__ import annotations
import logging

from aiohttp import web
from datetime import datetime, timedelta

from .logging_proxy import LoggingProxy
from .goodwedecoder import decode
from .const import *

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    ELECTRIC_CURRENT_AMPERE,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_KILO_WATT_HOUR,
    FREQUENCY_HERTZ,
    POWER_WATT,
    TIME_HOURS,
    TEMP_CELSIUS,
)

_LOGGER = logging.getLogger(DOMAIN)

class GoodWeProxyCoordinator(DataUpdateCoordinator):
    def __init__(self,  *args, serial_number, **kwargs,):
        super().__init__(*args, **kwargs)
        self.serial_number = serial_number
        proxy = LoggingProxy()
        proxy.add_parser("https://www.goodwe-power.com/Acceptor/Datalog", self.goodwe_decode)
        proxy.add_parser("http://www.goodwe-power.com/Acceptor/Datalog", self.goodwe_decode)
        self.last_data = None
        self.runner = web.AppRunner(proxy)

    async def setup(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, port=8180)
        await site.start()

    @property
    def has_recent_data(self):
        if self.last_data:
            return datetime.utcnow() - self.last_data <= timedelta(seconds=60)
        return False

    def goodwe_decode(self, event):
        try:
            data = decode(event['data'])
            if data.pop('device_id') == self.serial_number:
                self.last_data = datetime.utcnow()
                self.async_set_updated_data(data)
        except ValueError:
            _LOGGER.info(f"Skipped message: ({event})")


sensors = {
    'voltage_pv1': {
        "uom": ELECTRIC_POTENTIAL_VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'voltage_pv2': {
        "uom": ELECTRIC_POTENTIAL_VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'current_pv1': {
        "uom": ELECTRIC_CURRENT_AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'current_pv2': {
        "uom": ELECTRIC_CURRENT_AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'voltage_ac': {
        "uom": ELECTRIC_POTENTIAL_VOLT,
        "device_class": SensorDeviceClass.VOLTAGE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'current_ac': {
        "uom": ELECTRIC_CURRENT_AMPERE,
        "device_class": SensorDeviceClass.CURRENT,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'freq_ac': {
        "uom": FREQUENCY_HERTZ,
        "device_class": SensorDeviceClass.FREQUENCY,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'power_ac': {
        "uom": POWER_WATT,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'temperature': {
        "uom": TEMP_CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT
    },
    'kwh_total': {
        "uom": ENERGY_KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING
    },
    'hours_total': {
        "uom": TIME_HOURS,
        "device_class": "on_hours",
        "state_class": SensorStateClass.TOTAL_INCREASING
    },
    'kwh_daily': {
        "uom": ENERGY_KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING
    },
}


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities) -> bool:
    """Set up the Goodwe components from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    name = config_entry.title
    serial = config_entry.data[CONF_SERIAL]
    model = f"GW{serial[1:5]}-{serial[5:7]}"
    # Create update coordinator
    coordinator = GoodWeProxyCoordinator(
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
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    hass.data[DOMAIN][config_entry.entry_id] = {
        KEY_COORDINATOR: coordinator,
        KEY_DEVICE_INFO: device_info,
    }

    async_add_entities(
        GoodWeSensor(
            coordinator,
            tag=tag,
            **sensor,
            serial_number=serial,
            device_info=device_info,
        ) for tag, sensor in sensors.items())


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


class GoodWeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    @property
    def available(self) -> bool:
        return self.coordinator.has_recent_data

    def __init__(self, coordinator, tag, uom, device_class, state_class, serial_number, device_info):
        super().__init__(coordinator=coordinator)
        self._attr_name = tag
        self._attr_native_unit_of_measurement = uom
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"{DOMAIN}-{tag}-{serial_number}"
        self._attr_device_info = device_info


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data[self._attr_name]
        self.async_write_ha_state()




