import logging
from aiohttp import web
from aiohttp import ClientSession
from datetime import datetime as dt
from .const import DOMAIN

hostName = "localhost"
serverPort = 8180

logger = logging.getLogger(DOMAIN)


def generic_parser(event):
    logger.info(f"Unhandled event: {event}")


class LoggingProxy(web.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.router.add_route('*', '/{tail:.*}', self.handle)
        self.parsers = {}

    def add_parser(self, url, callback):
        self.parsers[url] = callback

    async def callback(self, event):
        if event['url'] in self.parsers:
            self.parsers[event["url"]](event)
        else:
            generic_parser(event)

    async def handle(self, server_request):
        if server_request.method == "CONNECT":
            await server_request.read()
        else:
            async with ClientSession() as session:
                method = server_request.method
                headers = dict(server_request.headers)
                url = f"https://{server_request.host}{server_request.rel_url}"
                data = await server_request.content.read()
                headers.pop('Host')

                async with session.request(
                        method,
                        url,
                        data=data,
                        headers=headers,
                ) as client_request:

                    r_headers = dict(client_request.headers)

                    for h in ("Transfer-Encoding", "Connection"):
                        r_headers.pop(h, None)

                    client_data = b""
                    while True:
                        chunk = await client_request.content.read()
                        if not chunk:
                            break
                        client_data += chunk

                    server_response = web.StreamResponse(
                        status=client_request.status,
                        headers=r_headers
                    )
                    await server_response.prepare(server_request)
                    await server_response.write(client_data)

                    event = {
                        "url": url,
                        "data": data,
                        "headers": headers,
                        "status_code": client_request.status,
                        "response": client_data,
                        "response_headers": r_headers,
                        "timestamp": dt.now(),
                    }
                    await self.callback(event)

                    return server_response

