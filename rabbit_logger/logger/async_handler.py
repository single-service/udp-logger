import asyncio
import json
import logging

from aio_pika import Message, connect_robust

from .base_handler import BaseLoggerHandler


class AsyncLoggerHandler(BaseLoggerHandler):
    def __init__(
        self, rabbit_host="localhost", rabbit_port=5672, rabbit_user="", rabbit_password="", server_name="python"
    ):
        super().__init__(rabbit_host, rabbit_port, rabbit_user, rabbit_password, server_name)
        self.connection = None
        self.channel = None

        # Подключение к RabbitMQ
        asyncio.create_task(self.connect())

    async def connect(self):
        try:
            self.connection = await connect_robust(
                host=self.host,
                port=self.port,
                login=self.user,
                password=self.password,
            )
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(self.queue, durable=True)
        except Exception as e:
            self.connection = None
            self.channel = None
            logging.error(f"AsyncLoggerHandler initialization failed: {e}")

    def emit(self, record):
        if not self.channel:
            logging.warning("AsyncLoggerHandler is not initialized properly; log message dropped.")
            return

        # Запускаем асинхронную задачу в текущем событийном цикле
        asyncio.create_task(self._emit_async(record))

    async def _emit_async(self, record):
        try:
            log_data = self.log_data(record)
            message = Message(body=json.dumps(log_data).encode())
            await self.channel.default_exchange.publish(message, routing_key=self.queue)
        except Exception as e:
            logging.error(f"AsyncLoggerHandler failed to send log: {e}")

    def close(self):
        if self.connection:
            asyncio.create_task(self.connection.close())
        super().close()
