import logging
import asyncio
from aiohttp import web
from aiohttp import ClientError, ClientSession, ClientTimeout
from goodwedecoder import decode_1phase

logger = logging.getLogger(__name__)

UPSTREAM_TIMEOUT = ClientTimeout(total=10)


class GoodWeProxy(web.Application):
    def __init__(self, port, datalog_callback):
        super().__init__()
        self.runner = web.AppRunner(self)
        self.port = port
        self.datalog_callback = datalog_callback
        self.add_routes([web.post("/Acceptor/Datalog", self.post_datalog)])
        self.add_routes([web.post("/Acceptor/GetSendInterval", self.post_sendinterval)])


    async def forward_request(self, server_request, data):
        headers = dict(server_request.headers)
        orig_host = headers.pop('Host')
        # GoodWe's server stopped answering over HTTPS; the inverter itself uses plain HTTP
        url = f"http://{orig_host}{server_request.path}"
        logger.debug(f'GOT: request, forwarding to {url}, data: {data}')
        try:
            async with ClientSession(timeout=UPSTREAM_TIMEOUT) as session:
                async with session.request(
                        server_request.method,
                        url,
                        data=data,
                        headers=headers,
                ) as client_request:
                    status = client_request.status
                    r_headers = dict(client_request.headers)
                    client_data = await client_request.read()
        except (ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Forwarding to {url} failed: {e!r}")
            return web.Response(status=502)

        for h in ("Transfer-Encoding", "Connection", "Content-Length", "Content-Encoding"):
            r_headers.pop(h, None)
        logger.debug(f"Response from {url}: {status} {client_data}")
        return web.Response(status=status, headers=r_headers, body=client_data)

    async def post_sendinterval(self, request):
        return await self.forward_request(request, await request.read())

    async def post_datalog(self, request):
        data = await request.read()
        # publish before forwarding, so an unreachable GoodWe server doesn't block local data
        try:
            message = decode_1phase(data)
            message['raw'] = data.hex()
            await self.datalog_callback(message)
        except ValueError:
            logger.debug(f"Skipped message: {data.hex()}")
        return await self.forward_request(request, data)

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