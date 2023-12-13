import json
import logging
import re
import socket
from datetime import datetime
from typing import List, Tuple, Union

import rfc5424logging
from tzlocal import get_localzone

log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(pathname)s - %(lineno)d - %(message)s"

DEFAULT_PROJECT_NAME = "default"


def setup(
    project_name: str,
    use_json: bool = True,
    log_level=logging.INFO,
    use_syslog: bool = False,
    address: Union[Tuple[str, int], str] = ("127.0.0.1", 1514),
    facility: int = rfc5424logging.LOG_USER,
    socket_type: socket.SocketKind = socket.SOCK_STREAM,
) -> None:
    if use_syslog:
        fmt = JsonFormatter(log_format, project_name=project_name)
        hdl = SysLogHandler(
            address=address,
            facility=facility,
            socktype=socket_type,
            msg_as_utf8=False,
        )
        hdl.setFormatter(fmt)
        hdl.set_project_name(project_name)
    else:
        if use_json:
            fmt = JsonFormatter(log_format, project_name=project_name)
        else:
            fmt = ISOFormatter(log_format, project_name=project_name)
        hdl = logging.StreamHandler()
        hdl.setFormatter(fmt)
    logging.basicConfig(handlers=[hdl], level=log_level)


class SysLogHandler(rfc5424logging.Rfc5424SysLogHandler):
    def get_appname(self, record):
        appname = getattr(record, "appname", self.appname)
        if appname is None or appname == "":
            appname = getattr(record, "name", self._project_name)
            if not appname.startswith(self._project_name):
                appname = "{}.{}".format(self._project_name, appname)
        return self.filter_printusascii(str(appname))

    def set_project_name(self, project_name: str) -> None:
        self._project_name = project_name


class ISOFormatter(logging.Formatter):
    def __init__(
        self,
        fmt=None,
        datefmt=None,
        style="%",
        project_name=DEFAULT_PROJECT_NAME,
        *args,
        **kwargs
    ):
        super().__init__(fmt, datefmt, style, *args, **kwargs)
        self._project_name = project_name

    def formatTime(self, record, datefmt=None):
        ts = datetime.fromtimestamp(record.created, get_localzone())
        return ts.isoformat()

    def format(self, record: logging.LogRecord) -> str:
        name = record.name
        if not name.startswith(self._project_name):
            name = "{}.{}".format(self._project_name, name)
        record.name = name
        return super().format(record)


class JsonFormatter(ISOFormatter):
    def __init__(
        self,
        fmt=None,
        datefmt=None,
        style="%",
        project_name=DEFAULT_PROJECT_NAME,
        *args,
        **kwargs
    ):
        super().__init__(fmt, datefmt, style, project_name, *args, **kwargs)
        self._required_fields = self.parse()

    def format(self, record: logging.LogRecord) -> str:
        name = record.name
        if not name.startswith(self._project_name):
            name = "{}.{}".format(self._project_name, name)
        record.name = name

        record.message = record.getMessage()
        if "asctime" in self._required_fields:
            record.asctime = self.formatTime(record, self.datefmt)
        log_record = {}
        for field in self._required_fields:
            log_record[field] = record.__dict__.get(field)
        if "msg_extra" in record.__dict__:
            log_record["msg_extra"] = record.__dict__["msg_extra"]

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            log_record["exc_info"] = record.exc_text
        try:
            if record.stack_info:
                log_record["stack_info"] = self.formatStack(record.stack_info)
        except AttributeError:
            # Python2.7 doesn't have stack_info.
            pass
        return json.dumps(log_record, ensure_ascii=False)

    def parse(self) -> List[str]:
        if isinstance(self._style, logging.StringTemplateStyle):
            formatter_style_pattern = re.compile(r"\$\{(.+?)\}", re.IGNORECASE)
        elif isinstance(self._style, logging.StrFormatStyle):
            formatter_style_pattern = re.compile(r"\{(.+?)\}", re.IGNORECASE)
        elif isinstance(self._style, logging.PercentStyle):
            formatter_style_pattern = re.compile(r"%\((.+?)\)", re.IGNORECASE)
        else:
            raise ValueError("Invalid format: %s" % self._fmt)

        if self._fmt:
            return formatter_style_pattern.findall(self._fmt)
        else:
            return []


class BaseLogger(logging.Logger):
    def makeRecord(
        self,
        name,
        level,
        fn,
        lno,
        msg,
        args,
        exc_info,
        func=None,
        extra=None,
        sinfo=None,
    ) -> None:
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.
        """
        rv = logging._logRecordFactory(
            name, level, fn, lno, msg, args, exc_info, func, sinfo
        )
        if extra is not None:
            if "msg_extra" in rv.__dict__:
                raise KeyError("Attempt to overwrite msg_extra in LogRecord")
            rv.__dict__["msg_extra"] = extra
        return rv


logging.setLoggerClass(BaseLogger)


if __name__ == "__main__":
    project_name = "test"
    setup(project_name)
    logger = logging.getLogger(project_name)
    log_msg = "this is a long long long long long long long long long long long message"
    import time

    child_logger = logger.getChild("child")
    child_logger.info("test child")

    try:
        1 / 0
    except Exception:
        child_logger.error("test error", exc_info=True)

    cnt = 1
    st = time.time()
    for _ in range(cnt):
        logger.info("hello world" * 100, extra={"a": "b", "c": "d"})
    et = time.time()
    print("cost:", et - st)
    print("avg_cost:", (et - st) / cnt)
