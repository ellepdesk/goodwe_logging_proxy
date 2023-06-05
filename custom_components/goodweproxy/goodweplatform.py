import logging
from aiohttp import web
from datetime import datetime, timedelta

from .logging_proxy import LoggingProxy
from .goodwedecoder import decode

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

_LOGGER = logging.getLogger(__name__)


class GoodWeProxyCoordinator(DataUpdateCoordinator):
    def __init__(self,  *args, serial_number, port, **kwargs,):
        super().__init__(*args, **kwargs)
        self.serial_number = serial_number
        self.port = port
        proxy = LoggingProxy()
        proxy.add_parser("https://www.goodwe-power.com/Acceptor/Datalog", self.goodwe_decode)
        proxy.add_parser("http://www.goodwe-power.com/Acceptor/Datalog", self.goodwe_decode)
        self.last_data = None
        self.runner = web.AppRunner(proxy)

    async def setup(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, port=self.port)
        await site.start()

    async def stop(self):
        await self.runner.shutdown()

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



