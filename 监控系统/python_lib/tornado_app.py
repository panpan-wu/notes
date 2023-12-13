from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler


class AppWithMetric(Application):
    def __init__(self, handlers, *args, **kwargs):
        super().__init__(handlers, *args, **kwargs)
        self._project = "default"
        self._stats_client = None

    def set_project(self, project: str) -> None:
        self._project = project

    def set_stats_client(self, stats_client) -> None:
        self._stats_client = stats_client

    def log_request(self, handler: RequestHandler) -> None:
        super().log_request(handler)
        self._observe_request(handler)

    def _observe_request(self, handler: RequestHandler) -> None:
        uri = handler.request.path
        method = handler.request.method
        request_time = handler.request.request_time()
        status = handler.get_status()
        if status == 404:
            return

        status_str = classify_status_code(status)
        if self._stats_client:
            if not isinstance(handler, WebSocketHandler):
                self._stats_client.timing(
                    "tornado_http_request_duration_seconds",
                    request_time * 1000,
                    tags={
                        "project": self._project,
                        "uri": uri,
                        "method": method,
                        "status": status_str,
                    },
                )
            self._stats_client.incr(
                "tornado_http_requests_total",
                tags={
                    "project": self._project,
                    "uri": uri,
                    "method": method,
                    "status": status_str,
                },
            )


def classify_status_code(status_code: int) -> str:
    if 100 <= status_code < 200:
        return "1xx"

    if 200 <= status_code < 300:
        return "2xx"

    if 300 <= status_code < 400:
        return "3xx"

    if 400 <= status_code < 500:
        return "4xx"

    if 500 <= status_code < 600:
        return "5xx"

    return "xxx"
