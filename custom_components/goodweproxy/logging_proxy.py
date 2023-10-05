import logging
from aiohttp import web
from aiohttp import ClientSession
from datetime import datetime as dt
from .const import DOMAIN

logger = logging.getLogger(DOMAIN)


def generic_parser(event):
    logger.info(f"Unhandled event: {event}")


class LoggingProxy(web.Application):
    def __init__(self, schema, host, path, callback):
        super().__init__()
        self.schema = schema
        self.host = host
        self.path = path
        self.callback = callback
        self.add_routes([web.post(path, self.handle)])

    async def _callback(self, event):
        return self.callback(event)

    async def handle(self, server_request):
        logger.warning(f"got {server_request}")
        if server_request.method == "CONNECT":
            await server_request.read()
        else:
            async with ClientSession() as session:
                method = server_request.method
                headers = dict(server_request.headers)
                orig_host = headers.pop('Host')
                url = f"{self.schema}{self.host}{self.path}"
                data = await server_request.content.read()

                async with session.request(
                        method,
                        url,
                        data=data,
                        headers=headers,
                ) as client_request:
                    status = client_request.status
                    r_headers = dict(client_request.headers)

                    client_data = b""
                    while True:
                        chunk = await client_request.content.read()
                        if not chunk:
                            break
                        client_data += chunk


                for h in ("Transfer-Encoding", "Connection"):
                    r_headers.pop(h, None)
                server_response = web.StreamResponse(
                    status=status,
                    headers=r_headers
                )
                await server_response.prepare(server_request)
                await server_response.write(client_data)

                event = {
                    "url": url,
                    "data": data,
                    "headers": headers,
                    "status_code": status,
                    "response": client_data,
                    "response_headers": r_headers,
                    "timestamp": dt.now(),
                }
                response = self._callback(event)
                if response != client_data:
                    print("expected: {response} got: {server_response}")

                return server_response

