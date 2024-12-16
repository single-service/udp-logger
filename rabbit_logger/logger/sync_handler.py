import datetime
import functools
import inspect
import json
import logging
import threading
import time
from uuid import uuid4

import pika

from .base_handler import BaseLoggerHandler


class SyncLoggerHandler(BaseLoggerHandler):
    _local = threading.local()  # Общее для всех экземпляров класса

    def __init__(
        self, rabbit_host="localhost", rabbit_port=5672, rabbit_user="", rabbit_password="", server_name="python"
    ):
        super().__init__(rabbit_host, rabbit_port, rabbit_user, rabbit_password, server_name)
        self._ensure_connection()

    def _ensure_connection(self):
        """
        Ленивая инициализация соединения и канала.
        """
        if not hasattr(self._local, "connection") or self._local.connection is None or self._local.connection.is_closed:
            try:
                self._local.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.host,
                        port=self.port,
                        credentials=pika.PlainCredentials(self.user, self.password),
                        # heartbeat=120,
                        # blocked_connection_timeout=30,
                    )
                )
                self._local.channel = self._local.connection.channel()
                self._local.channel.queue_declare(queue=self.queue, durable=True)
            except Exception as e:
                self._local.connection = None
                self._local.channel = None
                logging.error(f"SyncLoggerHandler failed to initialize connection: {e}")

    def emit(self, record):
        """
        Отправляет лог-сообщение в RabbitMQ.
        """
        self._ensure_connection()
        if not hasattr(self._local, "channel") or not self._local.channel:
            logging.warning("SyncLoggerHandler is not initialized properly; log message dropped.")
            return
        try:
            log_data = self.log_data(record)
            self._local.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.queue,
                body=json.dumps(log_data),
                properties=pika.BasicProperties(content_type="text/plain"),
            )
        except Exception as e:
            logging.error(f"SyncLoggerHandler failed to send log: {e}")
            self._local.connection = None  # Сброс соединения

    def close(self):
        """
        Закрывает соединение с RabbitMQ.
        """
        if hasattr(self._local, "connection") and self._local.connection:
            try:
                self._local.connection.close()
            except Exception as e:
                logging.error(f"SyncLoggerHandler failed to close connection: {e}")
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
            # Создаем временный экземпляр обработчика
            handler = cls(host="localhost", port=5672, user="user", password="password", server_name="my_server")

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
                    "created_dt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "func_path": func_path,
                    "func_name": func_name,
                    "exec_time": end_time - start_time,
                }
                handler.emit(logging.makeLogRecord({"msg": data}))
                handler.close()
            return result

        return wrapper
