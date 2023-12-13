import abc
import asyncio
import random
import time
from collections import deque
from functools import wraps


class Timer(object):
    """A context manager/decorator for statsd.timing()."""

    def __init__(self, client, stat, rate=1, tags=None):
        self.client = client
        self.stat = stat
        self.rate = rate
        self.tags = tags
        self.ms = None
        self._sent = False
        self._start_time = None

    def __call__(self, f):
        """Thread-safe timing function decorator."""

        @wraps(f)
        def _wrapped(*args, **kwargs):
            start_time = time.time()
            try:
                return_value = f(*args, **kwargs)
            finally:
                elapsed_time_ms = 1000.0 * (time.time() - start_time)
                self.client.timing(self.stat, elapsed_time_ms, self.rate)
            return return_value

        return _wrapped

    def __enter__(self):
        return self.start()

    def __exit__(self, typ, value, tb):
        self.stop()

    def start(self):
        self.ms = None
        self._sent = False
        self._start_time = time.time()
        return self

    def stop(self, send=True):
        if self._start_time is None:
            raise RuntimeError("Timer has not started.")
        dt = time.time() - self._start_time
        self.ms = 1000.0 * dt  # Convert to milliseconds.
        if send:
            self.send()
        return self

    def send(self):
        if self.ms is None:
            raise RuntimeError("No data recorded.")
        if self._sent:
            raise RuntimeError("Already sent data.")
        self._sent = True
        self.client.timing(self.stat, self.ms, self.rate, tags=self.tags)


class StatsClientBase(object):
    """A Base class for various statsd clients."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def _send(self):
        pass

    @abc.abstractmethod
    def pipeline(self):
        pass

    def timer(self, stat, rate=1):
        return Timer(self, stat, rate)

    def timing(self, stat, delta, rate=1, tags=None):
        """Send new timing information. `delta` is in milliseconds."""
        self._send_stat(stat, "%0.6f|ms" % delta, rate, tags=tags)

    def incr(self, stat, count=1, rate=1, tags=None):
        """Increment a stat by `count`."""
        self._send_stat(stat, "%s|c" % count, rate, tags=tags)

    def decr(self, stat, count=1, rate=1, tags=None):
        """Decrement a stat by `count`."""
        self.incr(stat, -count, rate, tags=tags)

    def gauge(self, stat, value, rate=1, delta=False, tags=None):
        """Set a gauge value."""
        if value < 0 and not delta:
            if rate < 1:
                if random.random() > rate:
                    return
            with self.pipeline() as pipe:
                pipe._send_stat(stat, "0|g", 1, tags=tags)
                pipe._send_stat(stat, "%s|g" % value, 1, tags=tags)
        else:
            prefix = "+" if delta and value >= 0 else ""
            self._send_stat(stat, "%s%s|g" % (prefix, value), rate, tags=tags)

    def set(self, stat, value, rate=1, tags=None):
        """Set a set value."""
        self._send_stat(stat, "%s|s" % value, rate, tags)

    def _send_stat(self, stat, value, rate, tags=None):
        self._after(self._prepare(stat, value, rate, tags=tags))

    def _prepare(self, stat, value, rate, tags=None):
        if rate < 1:
            if random.random() > rate:
                return
            value = "{}|@{}".format(value, rate)

        if self._prefix:
            stat = "{}.{}".format(self._prefix, stat)

        if tags:
            tag_string = ",".join(self._build_tag(k, v) for k, v in tags.items())
            return "{},{}:{}".format(stat, tag_string, value)
        return "{}:{}".format(stat, value)

    def _build_tag(self, tag, value):
        if value:
            return "{}={}".format(str(tag), str(value))
        else:
            return tag

    def _after(self, data):
        if data:
            self._send(data)


class TCPStatsClient(StatsClientBase):
    """TCP version of StatsClient."""

    def __init__(
        self, host="localhost", port=8125, prefix=None
    ):
        """Create a new client."""
        self._host = host
        self._port = port
        self._prefix = prefix
        self._writer = None

    def _send(self, data):
        """Send data to statsd."""
        self._writer.write(data.encode("ascii") + b"\n")

    async def connect(self):
        _, self._writer = await asyncio.open_connection(self._host, self._port)

    async def close(self):
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        self._writer = None

    def pipeline(self):
        return TCPPipeline(self)


class PipelineBase(StatsClientBase):
    __metaclass__ = abc.ABCMeta

    def __init__(self, client):
        self._client = client
        self._prefix = client._prefix
        self._stats = deque()

    @abc.abstractmethod
    def _send(self):
        pass

    def _after(self, data):
        if data is not None:
            self._stats.append(data)

    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        self.send()

    def send(self):
        if not self._stats:
            return
        self._send()

    def pipeline(self):
        return self.__class__(self)


class TCPPipeline(PipelineBase):
    def _send(self):
        self._client._after("\n".join(self._stats))
        self._stats.clear()


async def main():
    c = TCPStatsClient("localhost", 9125, prefix="test")
    await c.connect()
    c.incr("baz", tags={"type": "response"})


if __name__ == "__main__":
    asyncio.run(main())
