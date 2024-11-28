import datetime
import functools
import inspect
import json
import time
from uuid import uuid4

import pika
import psutil


class SyncAPMHandler:
    def __init__(
        self, rabbit_host="localhost", rabbit_port=5672, rabbit_user="", rabbit_password="", server_name="python"
    ):
        self.host = rabbit_host
        self.port = rabbit_port
        self.user = rabbit_user
        self.password = rabbit_password
        self.server_name = server_name
        self.queue = "apm"
        self.exchange = ""

        try:
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
            raise RuntimeError(f"SyncAPMHandler initialization failed: {e}")

    def send_apm_data(self, data):
        if not self.channel:
            raise RuntimeError("SyncAPMHandler is not initialized properly.")
        try:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.queue,
                body=json.dumps(data),
                properties=pika.BasicProperties(delivery_mode=2),
            )
        except Exception as e:
            raise RuntimeError(f"Failed to send APM data: {e}")

    def apm(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            func_path = inspect.getsourcefile(func)

            # Начало измерений
            cpu_usage_start = psutil.cpu_percent(interval=None)
            process = psutil.Process()
            ram_start = process.memory_info().rss
            start_time = time.time()

            try:
                # Вызов функции
                result = func(*args, **kwargs)
            except Exception as e:
                # Если функция выбрасывает исключение, можно логировать это
                raise e
            finally:
                # Конец измерений
                end_time = time.time()
                cpu_usage_end = psutil.cpu_percent(interval=None)
                ram_end = process.memory_info().rss

                # Вычисления
                exec_time = end_time - start_time
                cpu_time = cpu_usage_end - cpu_usage_start
                cpu_time = max(cpu_time, 0.0)
                ram_used = ram_end - ram_start
                ram_used = max(ram_used, 0.0)

                # Формирование данных для APM
                data = {
                    "uuid": str(uuid4()),
                    "created_dt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "func_path": func_path,
                    "func_name": func_name,
                    "exec_time": exec_time,
                    "cpu_used": cpu_time,
                    "ram_used": ram_used,
                    "server_name": self.server_name,
                }
                self.send_apm_data(data)

            return result  # Возвращаем результат единственного вызова функции

        return wrapper

    def close(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                raise RuntimeError(f"Failed to close connection: {e}")
