import datetime
import functools
import inspect
import json
import logging
import threading
import time
from uuid import uuid4
import socket

from .base_handler import BaseLoggerHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class UDPSyncLoggerHandler(BaseLoggerHandler):
    """
    Обработчик логов, отправляющий сообщения по UDP.
    """
    _local = threading.local()  # Можно использовать, если нужно хранить состояние

    def __init__(self, udp_host="localhost", udp_port=9999, server_name="python"):
        super().__init__(udp_host, udp_port, "", "", server_name)
        self.udp_host = udp_host
        self.udp_port = udp_port
        # Создаём UDP сокет один раз
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def emit(self, record):
        """
        Отправляет лог-сообщение по UDP.
        """
        try:
            log_data = self.log_data(record)
            message = json.dumps(log_data)
            self.sock.sendto(message.encode("utf-8"), (self.udp_host, self.udp_port))
        except Exception as e:
            logging.error(f"UDPSyncLoggerHandler failed to send log: {e}")

    def close(self):
        """
        Закрываем сокет при завершении.
        """
        if self.sock:
            self.sock.close()
        super().close()

    @classmethod
    def apm(cls, func):
        """
        Декоратор для сбора метрик выполнения функций.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("my_app")  # Имя логгера из LOGGING
            handler = next((h for h in logger.handlers if isinstance(h, cls)), None)
            if not handler:
                raise RuntimeError(f"{cls.__name__} is not configured in the logger.")

            func_name = func.__name__
            func_path = inspect.getsourcefile(func)
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                end_time = time.time()
                data = {
                    "uuid": str(uuid4()),
                    "created_dt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "func_path": func_path,
                    "func_name": func_name,
                    "exec_time": end_time - start_time,
                    "server_name": handler.server_name
                }
                # Отправляем лог через существующий handler
                handler.emit(logging.makeLogRecord({"msg": data}))
            return result

        return wrapper
