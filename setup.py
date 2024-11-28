from setuptools import setup, find_packages

setup(
    name="rabbit-logger",
    version="0.1.0",
    description="APM and logging library with RabbitMQ integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/single-service/rabbit-logger.git",  # Укажите ссылку на репозиторий
    author="Aleksey",
    author_email="your.email@example.com",
    license="MIT",
    packages=find_packages(),  # Найдет все пакеты в проекте
    install_requires=[
        "typing_extensions",
        "pika",       # RabbitMQ клиент
        "psutil",     # Для мониторинга ресурсов
        "aio_pika",   # Асинхронный RabbitMQ клиент
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
