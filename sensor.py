"""Platform for sensor integration."""
from __future__ import annotations

import logging

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

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import *

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

_LOGGER = logging.getLogger(__name__)

sensors = {
    # 'device_id': 'XXXXXXXXXXXXXXX',
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
        "state_class": SensorStateClass.MEASUREMENT
    },
    'hours_total': {
        "uom": TIME_HOURS,
        "device_class": "on_hours",
        "state_class": SensorStateClass.MEASUREMENT
    },
    'kwh_daily': {
        "uom": ENERGY_KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.MEASUREMENT
    },
}


async def async_setup_entry(
        hass,
        config_entry,
        async_add_entities
):
    """Config entry example."""
    # assuming API object stored here by __init__.py
    # entities: list[InverterSensor] = []
    # proxy = hass.data[DOMAIN][config_entry.entry_id][KEY_PROXY]
    coordinator = hass.data[DOMAIN][config_entry.entry_id][KEY_COORDINATOR]
    # device_info = hass.data[DOMAIN][config_entry.entry_id][KEY_DEVICE_INFO]

    await coordinator.async_refresh()
    async_add_entities(InverterSensor(coordinator, tag=tag, **sensor) for tag, sensor in sensors.items())


class InverterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, tag, uom, device_class, state_class):
        super().__init__(coordinator=coordinator)
        self._attr_name = tag
        self._attr_native_unit_of_measurement = uom
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data[self._attr_name]
        self.async_write_ha_state()




