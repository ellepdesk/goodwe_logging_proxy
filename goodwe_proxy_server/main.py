import os
import asyncio
import logging
from goodweproxy import GoodWeProxy
from goodwemqttclient import MqttClient

port = os.environ.get('PORT', 80)
mqtt_host = os.environ.get('MQTT_HOST', 'localhost')
loglevel = os.environ.get('LOGLEVEL', 'INFO')

async def main():
    mqtt = MqttClient(hostname=mqtt_host)
    proxy = GoodWeProxy(port=port, datalog_callback=mqtt.push)
    await proxy.setup()
    try:
        await mqtt.run()
    finally:
        await proxy.stop()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(name)s:%(levelname)s:%(message)s', level=loglevel)

    asyncio.run(main())