import json
from homeassistant.const import Platform

with open('manifest.json') as f:
    data = json.load(f)

DOMAIN = data["domain"]
DEFAULT_NAME = data["name"]
CONF_SERIAL = "serial"

KEY_PROXY = "inverter"
KEY_COORDINATOR = "coordinator"
KEY_DEVICE_INFO = "device_info"

PLATFORMS = [Platform.NUMBER, Platform.SELECT, Platform.SENSOR]