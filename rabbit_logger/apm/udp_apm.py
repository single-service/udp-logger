import datetime
import functools
import inspect
import json
import time
from uuid import uuid4

import psutil
import socket


class UdpAPMHandler:
    def __init__(self, udp_host="localhost", udp_port=9999, server_name="python"):
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.server_name = server_name

        # Создаем UDP сокет для отправки APM данных
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_apm_data(self, data):
        """
        Отправляет APM данные по UDP.
        """
        try:
            message = json.dumps(data).encode("utf-8")
            self.sock.sendto(message, (self.udp_host, self.udp_port))
        except Exception as e:
            raise RuntimeError(f"Failed to send APM data over UDP: {e}")

    def apm(self, func):
        """
        Декоратор для сбора метрик выполнения функций.
        """

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
                # Можно логировать ошибку, если нужно
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
                    "created_dt": datetime.datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S.%f"
                    ),
                    "func_path": func_path,
                    "func_name": func_name,
                    "exec_time": exec_time,
                    "cpu_used": cpu_time,
                    "ram_used": ram_used,
                    "server_name": self.server_name,
                }
                self.send_apm_data(data)

            return result

        return wrapper

    def close(self):
        """
        Закрываем сокет.
        """
        if self.sock:
            self.sock.close()
