from homeassistant.const import Platform


DOMAIN = "goodweproxy"
DEFAULT_NAME = "GoodWe Inverter"
CONF_SERIAL = "serial"

KEY_PROXY = "inverter"
KEY_COORDINATOR = "coordinator"
KEY_DEVICE_INFO = "device_info"
KEY_RUNNNER = "runner"

PLATFORMS = [Platform.SENSOR]
