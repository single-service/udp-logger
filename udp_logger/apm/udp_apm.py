import asyncio
import datetime
import functools
import inspect
import json
import random
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
            message = json.dumps({
                "type": "apm",
                "collection": "apm",
                "message": data
            }).encode("utf-8")
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


class UdpAsyncAPMHandler:
    def __init__(self, udp_host="localhost", udp_port=9999, server_name="python"):
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.server_name = server_name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_apm_data(self, data: dict) -> None:
        try:
            message = json.dumps({
                "type": "apm",
                "collection": "apm",
                "message": data
            }).encode("utf-8")
            self.sock.sendto(message, (self.udp_host, self.udp_port))
        except Exception:
            # Не роняем приложение из-за телеметрии
            # при желании — залогируйте
            pass

    def apm(self, func):
        """
        Декоратор, корректно работающий и с sync, и с async функциями.
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            func_path = inspect.getsourcefile(func)

            process = psutil.Process()
            mem_start = process.memory_info().rss
            cpu_start = process.cpu_times()
            t0 = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                raise e
            finally:
                t1 = time.perf_counter()
                cpu_end = process.cpu_times()
                mem_end = process.memory_info().rss

                exec_time = t1 - t0
                cpu_used = ((cpu_end.user + cpu_end.system) - (cpu_start.user + cpu_start.system))
                ram_used = max(mem_end - mem_start, 0)

                data = {
                    "uuid": str(uuid4()),
                    "created_dt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "func_path": func_path,
                    "func_name": func_name,
                    "exec_time": exec_time,
                    "cpu_used": cpu_used,
                    "ram_used": ram_used,
                    "server_name": self.server_name,
                }
                self.send_apm_data(data)
        return wrapper

        
    def close(self):
        if self.sock:
            self.sock.close()


# Тестовая асинхронная функция
async def test_apm_function(sleep_time):
    print(f"Start sleeping for {sleep_time:.2f} seconds...")
    await asyncio.sleep(sleep_time)
    print("Sleep finished.")

async def main_test():
    tasks = []
    num_tests = 5  # Количество тестов
    
    for _ in range(num_tests):
        sleep_time = random.uniform(0.1, 1.0)  # Генерируем случайное время сна между 0.1 и 1 секундой
        task = wrapped_test_function(sleep_time)
        tasks.append(task)
    
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    UDP_HOST = "" # Need to add
    UDP_PORT = 9999 # Need to add
    SERVER_NAME = "test_apm" # Need to add
    # Инициализация
    UDPHandler = UdpAPMHandler(
        udp_host=UDP_HOST,
        udp_port=UDP_PORT,
        server_name=SERVER_NAME
    )

    # Применяем декорацию к нашей тестовой функции
    wrapped_test_function = UDPHandler.apm(test_apm_function)
    asyncio.run(main_test())
