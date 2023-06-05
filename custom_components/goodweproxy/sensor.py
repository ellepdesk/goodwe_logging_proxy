from typing import TYPE_CHECKING


from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, GOODWE_COORDINATOR, GOODWE_DEVICE_INFO


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


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SMA sensors."""
    sma_data = hass.data[DOMAIN][config_entry.entry_id]

    coordinator = sma_data[GOODWE_COORDINATOR]
    device_info = sma_data[GOODWE_DEVICE_INFO]

    if TYPE_CHECKING:
        assert config_entry.unique_id

    entities = []
    for sensor in sensors:


        entities.append(
               GoodWeSensor(
            coordinator,
            tag=tag,
            **sensor,
            config_entry_unique_id=config_entry.unique_id,
            device_info=device_info,
        ) for tag, sensor in sensors.items())
    )

    async_add_entities(entities)

class GoodWeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    @property
    def available(self) -> bool:
        return self.coordinator.has_recent_data

    def __init__(
            self,
            coordinator: DataUpdateCoordinator,
            tag,
            uom,
            device_class,
            state_class,
            config_entry_unique_id,
            device_info,
            ):
        super().__init__(coordinator=coordinator)
        self._attr_name = tag
        self._attr_native_unit_of_measurement = uom
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = f"{DOMAIN}-{config_entry_unique_id}-{tag}"
        self._attr_device_info = device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data[self._attr_name]
        self.async_write_ha_state()

