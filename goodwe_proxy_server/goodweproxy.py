import logging
from aiohttp import web
from aiohttp import ClientSession
from datetime import datetime as dt
from goodwedecoder import decode_1phase

logger = logging.getLogger(__name__)


class GoodWeProxy(web.Application):
    def __init__(self, port, datalog_callback):
        super().__init__()
        self.runner = web.AppRunner(self.proxy)
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
                logger.warning(f'GOT: data: {data}')

                url = f"http://{orig_host}/Acceptor/Datalog"
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
            return event

    async def post_sendinterval(self, request):
        event = self.forward_request(request)
        logger.info(f"GetSendInterval: {event}")

    async def post_datalog(self, request):
        event = self.forward_request(request)
        try:
            data = decode_1phase(event['data'])
            data['raw'] = event['data'].hex()
            data['response_raw'] = event['response'].hex()
        except ValueError:
            logger.info(f"Skipped message: ({event})")
        await self.datalog_callback(data)

    async def post_datalog(self, server_request):
        if server_request.method == "CONNECT":
            await server_request.read()
        else:
            async with ClientSession() as session:
                method = server_request.method
                headers = dict(server_request.headers)
                orig_host = headers.pop('Host')
                data = await server_request.content.read()
                logger.warning(f'GOT: data: {data}')

                url = f"http://{orig_host}/Acceptor/Datalog"
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
                try:
                    data = decode_1phase(event['data'])
                    data['raw'] = event['data'].hex()
                    data['response_raw'] = event['response'].hex()
                except ValueError:
                    logger.info(f"Skipped message: ({event})")

                await self.datalog_callback(data)
                return server_response

    async def setup(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, port=self.port)
        await site.start()

    async def stop(self):
        await self.runner.shutdown()
