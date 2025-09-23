.PHONY: setup lint test build validate

setup:
	pip install -r requirements.txt
	pip install ruff

lint:
	ruff check src tests

test:
	pytest -q

build:
	python src/cli.py build

validate:
	python src/cli.py validate
