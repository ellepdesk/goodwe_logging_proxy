import os
import json
import aiomqtt
import asyncio
import logging
from asyncio.exceptions import CancelledError

logger = logging.getLogger(__name__)

sensors = [
    {
        "name": "DC Voltage String 1",
        "tag": "voltage_pv1",
        "uom": "V",
        "device_class": "voltage",
        "state_class": "measurement",
    },
    {
        "name": "DC Voltage String 2",
        "tag": "voltage_pv2",
        "uom": "V",
        "device_class": "voltage",
        "state_class": "measurement",
    },
    {
        "name": "DC Current String 1",
        "tag": "current_pv1",
        "uom": "A",
        "device_class": "current",
        "state_class": "measurement",
    },
    {
        "name": "DC Current String 2",
        "tag": "current_pv2",
        "uom": "A",
        "device_class": "current",
        "state_class": "measurement",
    },
    {
        "name": "AC Voltage",
        "tag": "voltage_ac",
        "uom": "V",
        "device_class": "voltage",
        "state_class": "measurement",
    },
    {
        "name": "AC Current",
        "tag": "current_ac",
        "uom": "A",
        "device_class": "current",
        "state_class": "measurement",
    },
    {
        "name": "AC Frequency",
        "tag": "freq_ac",
        "uom": "Hz",
        "device_class": "frequency",
        "state_class": "measurement",
    },
    {
        "name": "AC Power",
        "tag": "power_ac",
        "uom": "W",
        "device_class": "power",
        "state_class": "measurement",
    },
    {
        "name": "Inverter Temperature",
        "tag": "temperature",
        "uom": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    {
        "name": "Total Generated Energy",
        "tag": "kwh_total",
        "uom": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
    {
        "name": "Operating Hours",
        "tag": "hours_total",
        "uom": "h",
        "device_class": "duration",
        "state_class": "total_increasing",
    },
    {
        "name": "Daily Generated Energy",
        "tag": "kwh_daily",
        "uom": "kWh",
        "device_class": "energy",
        "state_class": "total_increasing",
    },
]

discovery_prefix = "homeassistant"
component = "sensor"


class MqttClient:
    def __init__(self, hostname: str) -> None:
        self.hostname = hostname
        self.known_serials = set()
        self.message_queue = asyncio.Queue()

    async def run(self):
        try:
            async with aiomqtt.Client(hostname=self.hostname) as client:
                await self.publish_queue(client)
        except (KeyboardInterrupt, CancelledError):
            pass

    async def publish_discovery(self, client: aiomqtt.Client, serial):
        node_id = f"goodwe_{serial}"
        topic_prefix = f"{discovery_prefix}/{component}/{node_id}"
        state_topic = f"{topic_prefix}/state"
        object_id = "goodwe"
        expire_after_s = 600

        for s in sensors:
            object_id = s["tag"]

            discovery_topic = f"{topic_prefix}/{object_id}/config"
            discovery_message = {
                "name": s["name"],
                "device_class": s["device_class"],
                "state_class": s["state_class"],
                "unit_of_measurement": s["uom"],
                "state_topic": state_topic,
                "unique_id": f"{object_id}_{serial}",
                "value_template": "{{ value_json." + f"{object_id}" + " }}",
                "device": {
                    "identifiers": [f"{serial}"],
                    "name": "GoodWe Inverter",
                    "manufacturer": "GoodWe",
                    "model": "GW-3600-DS",
                },
            }
            if s["state_class"] == "measurement":
                discovery_message["expire_after"] = expire_after_s
            await client.publish(
                discovery_topic,
                json.dumps(discovery_message, indent=2),
                retain=True,
            )

    async def publish_queue(self, client: aiomqtt.Client):
        while True:
            message = await self.message_queue.get()
            serial = message.get("device_id")
            if serial not in self.known_serials:
                self.known_serials.add(serial)
                await self.publish_discovery(client, serial)

            node_id = f"goodwe_{serial}"
            topic = f"{discovery_prefix}/{component}/{node_id}/state"
            logger.info(f"mqtt message: f{message} on topic: {topic}")
            await client.publish(topic, json.dumps(message, indent=2))

    async def push(self, message: dict):
        await self.message_queue.put(message)
