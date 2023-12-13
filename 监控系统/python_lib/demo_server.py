import sys

import tornado
from tornado.web import RequestHandler

from .stats_client import TCPStatsClient
from .tornado_app import AppWithMetric
from .log import setup as setup_log


class GreetHandler(RequestHandler):
    def get(self):
        self.write("Hello, world")


def make_app(project: str) -> AppWithMetric:
    app = AppWithMetric(
        handlers=[
            (r"/greet", GreetHandler),
        ],
    )
    app.set_project(project)
    return app


if __name__ == "__main__":
    project = "demo"
    port = int(sys.argv[1])
    app = make_app(project)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.bind(port)
    http_server.start()

    setup_log(project, use_json=True)
    loop = tornado.ioloop.IOLoop.current()
    stats_client = TCPStatsClient("localhost", 9125)
    loop.add_callback(stats_client.connect)
    app.set_stats_client(stats_client)

    loop.start()
