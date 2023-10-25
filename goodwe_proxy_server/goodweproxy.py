import logging
import asyncio
from aiohttp import web
from aiohttp import ClientSession
from datetime import datetime as dt
from goodwedecoder import decode_1phase

logger = logging.getLogger(__name__)


class GoodWeProxy(web.Application):
    def __init__(self, port, datalog_callback):
        super().__init__()
        self.runner = web.AppRunner(self)
        self.port = port
        self.datalog_callback = datalog_callback
        self.add_routes([web.post("/Acceptor/Datalog", self.post_datalog)])
        self.add_routes([web.post("/Acceptor/GetSendInterval", self.post_sendinterval)])


    async def forward_request(self, server_request):
        if server_request.method == "CONNECT":
            await server_request.read()
        else:
            async with ClientSession() as session:
                method = server_request.method
                headers = dict(server_request.headers)
                orig_host = headers.pop('Host')
                data = await server_request.content.read()
                path = server_request.path
                url = f"https://{orig_host}/{path}"
                logger.debug(f'GOT: request, forwarding to {url}, data: {data}')
                async with session.request(
                        method,
                        url,
                        data=data,
                        headers=headers,
                ) as client_request:
                    status = client_request.status
                    r_headers = dict(client_request.headers)

                    client_data = b""
                    while (chunk := await client_request.content.read()):
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
            return event

    async def post_sendinterval(self, request):
        event = await self.forward_request(request)
        logger.debug(f"GetSendInterval: {event}")

    async def post_datalog(self, request):
        event = await self.forward_request(request)
        try:
            data = decode_1phase(event['data'])
            data['raw'] = event['data'].hex()
            data['response_raw'] = event['response'].hex()
            await self.datalog_callback(data)
        except ValueError:
            logger.debug(f"Skipped message: ({event})")

    async def setup(self):
        await self.runner.setup()
        logger.info(f"Starting webserver at port: {self.port}")
        site = web.TCPSite(self.runner, port=self.port)
        await site.start()

    async def stop(self):
        await self.runner.shutdown()


if __name__ == "__main__":
    async def callback(msg):
        print(msg)

    async def main():
        try:
            proxy = GoodWeProxy(port=8099, datalog_callback=callback)
            await proxy.setup()
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass

    asyncio.run(main())