import logging
from aiohttp import web
from datetime import datetime, timedelta

from logging_proxy import LoggingProxy
from goodwedecoder import decode

_LOGGER = logging.getLogger(__name__)


class GoodWeProxy():
    def __init__(self, *args, port, **kwargs,):
        super().__init__(*args, **kwargs)
        self.port = port
        self.proxy = LoggingProxy(
            schema="http://",
            host="www.goodwe-power.com",
            path="/Acceptor/Datalog",
            callback=self.goodwe_decode,
        )
        self.last_data = None
        self.runner = web.AppRunner(self.proxy)
        self.callback = None

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

    async def goodwe_decode(self, event):
        _LOGGER.info(f"goodwe_decode({event})")

        try:
            data = decode(event['data'])
            data['raw'] = event['data'].hex()
            data['response_raw'] = event['response'].hex()
            self.last_data = datetime.utcnow()
            if self.callback:
                await self.callback(data)
            return data.get('device_id')
        except ValueError:
            _LOGGER.info(f"Skipped message: ({event})")
