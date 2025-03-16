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
            message = json.dumps({
                "type": "logs",
                "collection": "logs",
                "message": log_data
            })
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
