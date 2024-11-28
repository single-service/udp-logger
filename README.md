
# Rabbit-logger

`rabbit-logger` — это библиотека для интеграции APM (Application Performance Monitoring) и логирования с RabbitMQ. Она предоставляет интерфейс для отслеживания метрик функций и удобное логирование через синхронные и асинхронные обработчики. Логи и метрики записываются в RabbitMq и в дальнейшем вы можете развернуть у себя образ из Dockerhub [клик] (тут будет ссылка), где данные логи будут записываться в БД clickhouse, и с помощью интерфейса Metabase вы сможете просматривать логи и информацию о своих функциях из своих сервисов.

---

## Установка

Установите библиотеку с помощью pip:

```bash
pip install rabbit-logger
```

---

## Настройка логирования

Добавьте обработчики в конфигурацию `LOGGING`. Вы можете выбрать синхронный или асинхронный обработчик.

### Пример настройки:

```python
from logging.config import dictConfig
import logging

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(message)s"},
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "rabbit-logger": {
            "level": "INFO",
            "class": "rabbit_logger.logger.async_handler.AsyncLoggerHandler",  # Для асинхронного логгера или 'apmlogger.logger.sync_handler.SyncLoggerHandler' для синхронного
            "host": "localhost",
            "port": 5672,
            "user": "user",
            "password": "password",
            "server_name": "my_server",  # Название вашего сервера
        },
        "console": {
            "level": "DEBUG",  # Уровень логов для консоли
            "class": "logging.StreamHandler",
            "formatter": "simple",  # Форматирование логов в консоли
        },
    },
    "loggers": {
        "my_app": {
            "handlers": ["rabbit-logger", "console"],  # Используем rabbit-logger и консольный обработчики
            "level": "INFO",  # Уровень логов для логгера
            "propagate": True,
        },
    },
}

# Применяем конфигурацию
dictConfig(LOGGING)

# Создаем логгер
logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)

# Пример использования
logger.info("Это информационное сообщение!")
logger.error("Ошибка!")
```

---

## Использование APM

### Синхронный APM

Для синхронного мониторинга создайте экземпляр `SyncAPMHandler`:

```python
from rabbit_logger.apm.sync_apm import SyncAPMHandler

# Создаем обработчик APM
APMHandler = SyncAPMHandler(
    rabbit_host="localhost",
    rabbit_port=5672,
    rabbit_user="user",
    rabbit_password="password",
    server_name="my_server"
)

@APMHandler.apm
def my_sync_function():
    print("Выполнение функции...")
    time.sleep(2)
    return "Готово!"

result = my_sync_function()
print(result)
```

### Асинхронный APM

Для асинхронного мониторинга используйте `AsyncAPMHandler`:

```python
import asyncio
from rabbit_logger.apm.async_apm import AsyncAPMHandler

# Создаем обработчик APM
APMHandler = AsyncAPMHandler(
    rabbit_host="localhost",
    rabbit_port=5672,
    rabbit_user="user",
    rabbit_password="password",
    server_name="my_server"
)

async def main():
    await APMHandler.connect()

    @APMHandler.apm
    async def my_async_function():
        print("Выполнение асинхронной функции...")
        await asyncio.sleep(2)
        return "Готово!"

    result = await my_async_function()
    print(result)

    await APMHandler.close()

asyncio.run(main())
```

---

## Обязательные параметры

1. **RabbitMQ параметры**:
   - `rabbit_host` — Адрес сервера RabbitMQ.
   - `rabbit_port` — Порт сервера RabbitMQ.
   - `rabbit_user` — Логин для подключения.
   - `rabbit_password` — Пароль для подключения.

2. **Серверное имя (`server_name`)**:
   - Полезно для идентификации, с какого сервера были отправлены метрики или логи.

---

## Лицензия

Этот проект лицензирован под [MIT License](LICENSE).

---

## Обратная связь

Если у вас есть вопросы, предложения или вы нашли ошибку, создайте issue в [GitHub репозитории](https://github.com/single-service/rabbit-logger.git).