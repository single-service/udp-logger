import datetime
import functools
import inspect
import json
import logging
import time
from uuid import uuid4

import pika

from .base_handler import BaseLoggerHandler


class SyncLoggerHandler(BaseLoggerHandler):
    def __init__(
        self, rabbit_host="localhost", rabbit_port=5672, rabbit_user="", rabbit_password="", server_name="python"
    ):
        super().__init__(rabbit_host, rabbit_port, rabbit_user, rabbit_password, server_name)
        try:
            # Подключение к RabbitMQ
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=pika.PlainCredentials(self.user, self.password),
                )
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue, durable=True)
        except Exception as e:
            self.connection = None
            self.channel = None
            logging.error(f"SyncLoggerHandler initialization failed: {e}")

    def emit(self, record):
        """
        Отправляет лог-сообщение в RabbitMQ.
        """
        if not self.channel:
            logging.warning("SyncLoggerHandler is not initialized properly; log message dropped.")
            return
        try:
            log_data = self.log_data(record)
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.queue,
                body=json.dumps(log_data),
                properties=pika.BasicProperties(delivery_mode=2),  # Делает сообщение устойчивым
            )
        except Exception as e:
            logging.error(f"SyncLoggerHandler failed to send log: {e}")

    def close(self):
        """
        Закрывает соединение с RabbitMQ.
        """
        if self.connection:
            try:
                self.connection.close()
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
            print("--------------")
            logger = logging.getLogger("my_app")  # Имя логгера из LOGGING
            handler = next((h for h in logger.handlers if isinstance(h, cls)), None)
            if not handler:
                raise RuntimeError(f"{cls.__name__} is not configured in the logger.")
            print("==========", handler)
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
