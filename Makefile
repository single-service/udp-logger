format:
	black .
	isort .

lint:
	black --check .
	isort --check .
	flake8 --inline-quotes '"'
	pylint $(shell git ls-files '*.py')
	PYTHONPATH=/ mypy --namespace-packages --show-error-codes . --check-untyped-defs --ignore-missing-imports --show-traceback

run_test:
	python3 setup.py sdist bdist_wheel
	pip install dist/traderhub_tradeanalytica-0.0.3-py3-none-any.whl
	python3 -m unittest test_backtest.py

public:
	python3 setup.py sdist bdist_wheel
	twine check dist/*
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*