from homeassistant.const import Platform


DOMAIN = "goodweproxy"
DEFAULT_NAME = "GoodWe Inverter"
CONF_SERIAL = "serial"

GOODWE_COORDINATOR = "coordinator"
GOODWE_DEVICE_INFO = "device_info"

PLATFORMS = [Platform.SENSOR]
