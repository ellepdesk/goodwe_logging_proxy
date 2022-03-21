from homeassistant.const import Platform


DOMAIN = "goodweproxy"
DEFAULT_NAME = "GoodWe Inverter"
CONF_SERIAL = "serial"

KEY_COORDINATOR = "coordinator"
KEY_DEVICE_INFO = "device_info"

PLATFORMS = [Platform.SENSOR]
