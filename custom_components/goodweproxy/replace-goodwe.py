import logging
from aiohttp import web
from aiohttp import ClientSession
from datetime import datetime as dt
from .const import DOMAIN

logger = logging.getLogger(DOMAIN)


def generic_parser(event):
    logger.info(f"Unhandled event: {event}")


class LoggingProxy(web.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = kwargs.pop('url')
        self.path = kwargs.pop('path')
        self.add_routes([web.post(self.path, self.handle)])
        self.parsers = {}

    def add_parser(self, url, callback):
        self.parsers[url] = callback

    async def callback(self, event):
        if event['url'] in self.parsers:
            return self.parsers[event["url"]](event)
        else:
            return generic_parser(event)

    async def handle(self, server_request):
        logger.warning(f"got {server_request}")
        if server_request.method == "CONNECT":
            await server_request.read()
        else:
            url = f"{self.url}{self.path}"

            if url not in self.parsers:
                server_response = web.StreamResponse(
                        status=200,
                    )
                await server_response.prepare(server_request)
                await server_response.write(b"NOT HANDLED\n")
            else:
                try:
                    data = await server_request.content.read()
                    status=200
                    server_response = web.StreamResponse(
                        status=status,
                    )
                    await server_response.prepare(server_request)
                    event = {
                        "url": url,
                        "data": data,
                        "status_code": status,
                        "timestamp": dt.now(),
                    }
                    serial = await self.callback(event)
                    response = serial.encode('ascii') + bytes.fromhex("00 00 00 00 03 84")
                    await server_response.write(response)

                except:
                    logger.exception(f"error processing {server_request}")
                    raise

            return server_response

