from setuptools import setup, find_packages

setup(
    name="udp-logger",
    version="1.0.0",
    description="APM and logging library with UDP integration",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/single-service/udp-logger.git",  # Укажите ссылку на репозиторий
    author="Aleksey Rybkin, Dmitriy Sosedov",
    author_email="singleservice2022@gmail.com",
    license="MIT",
    packages=find_packages(),  # Найдет все пакеты в проекте
    install_requires=[
        "typing_extensions",
        "psutil",     # Для мониторинга ресурсов
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
