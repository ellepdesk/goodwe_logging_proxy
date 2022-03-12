# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import logging
import requests
from queue import Queue
from threading import Thread, Event
from collections.abc import Callable
from goodwedecoder import decode

hostName = "localhost"
serverPort = 8180

events = Queue()

def goodwe_decode(event):
    logging.info(decode(event['data']))


class ProxyProcessor():
    def __init__(self):
        self._stop = Event()
        self.parsers = {}

    def add_parser(self, url: str, parser: Callable):
        self.parsers[url] = parser

    def stop(self):
        self._stop.set()
        events.put(None)

    def run(self):
        while not self._stop.is_set():
            event = events.get()
            if event:
                logging.debug(f"Processing: {event}")

                if event['url'] in self.parsers:
                    self.parsers[event["url"]](event)

    def start(self):
        th = Thread(target=self.run)
        th.start()


class PostProxy(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))  # <--- Gets the size of data
        post_data = self.rfile.read(content_length)  # <--- Gets the data itself

        host = self.headers["Host"]
        path = self.path
        url = f"https://{host}{path}"

        event = {
            "url": url,
            "data": post_data,
            "headers": {k: v for k, v in self.headers.items()}
        }

        logging.debug(f"POST: {url}, {post_data}")
        r = requests.post(url, post_data, headers=self.headers)

        event["status_code"] = r.status_code
        event["response"] = r.content
        event["response_headers"] = r.headers

        self.send_response(r.status_code)

        try:
            r.headers.pop("Transfer-Encoding")
        except KeyError:
            pass

        try:
            r.headers.pop("Connection")
        except KeyError:
            pass

        for h, val in r.headers.items():
            self.send_header(h, val)

        self.end_headers()
        self.wfile.write(r.content)

        events.put(event)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    webServer = HTTPServer((hostName, serverPort), PostProxy)
    logging.info("Server started http://%s:%s" % (hostName, serverPort))
    processor = ProxyProcessor()
    processor.add_parser('https://www.goodwe-power.com/Acceptor/Datalog', goodwe_decode)
    try:
        processor.start()
        webServer.serve_forever()
    except KeyboardInterrupt:
        processor.stop()
        pass

    webServer.server_close()
    logging.info("Server stopped")
