import logging
import traceback


class BaseLoggerHandler(logging.Handler):
    def __init__(self, host, port, user, password, server_name):
        super().__init__()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.server_name = server_name
        self.queue = "logs"
        self.exchange = ""

        if not self.user or not self.password:
            raise ValueError("RabbitMQ configuration is missing required parameters (user, password)")

    @staticmethod
    def format_exception(ei) -> str:
        """
        Форматирует исключение в строку.
        """
        tb = ei[2]
        return "".join(traceback.format_exception(ei[0], ei[1], tb)).strip()

    def log_data(self, record):
        """
        Формирует структуру лога для отправки.
        """
        import datetime
        from uuid import uuid4

        data = {
            "uuid": str(uuid4()),
            "created_dt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "pathname": str(getattr(record, "pathname", "")),
            "funcName": str(getattr(record, "funcName", "")),
            "lineno": getattr(record, "lineno", 0),
            "message": record.getMessage(),
            "exc_text": str(getattr(record, "exc_text", "")),
            "created": getattr(record, "lineno", 0),
            "filename": str(getattr(record, "filename", "")),
            "levelname": str(getattr(record, "levelname", "")),
            "levelno": str(getattr(record, "levelno", "")),
            "module": str(getattr(record, "module", "")),
            "msecs": getattr(record, "msecs", 0),
            "msg": str(getattr(record, "msg", "")),
            "name": str(getattr(record, "name", "")),
            "process": str(getattr(record, "process", "")),
            "processName": str(getattr(record, "processName", "")),
            "relativeCreated": str(getattr(record, "relativeCreated", "")),
            "stack_info": str(getattr(record, "stack_info", "")),
            "thread": str(getattr(record, "thread", "")),
            "threadName": str(getattr(record, "threadName", "")),
            "server_name": self.server_name,
        }
        if record.exc_info:
            data["exc_text"] = self.format_exception(record.exc_info)
        return data
