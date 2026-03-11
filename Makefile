.PHONY: dev test lint install db-up db-down setup-hooks

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn
PYTEST = $(VENV)/bin/pytest
PRECOMMIT = $(VENV)/bin/pre-commit

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements-dev.txt

setup-hooks:
	$(PRECOMMIT) install
	$(PRECOMMIT) install --hook-type pre-push

dev:
	mkdir -p data/backups/basebackup data/backups/pg_dump data/backups/logs
	$(UVICORN) app.main:app --host 127.0.0.1 --port 8001 --reload

test:
	$(PYTEST)

test-fast:
	$(PYTEST) --no-cov -x

db-up:
	docker compose -f docker-compose.dev.yml up -d

db-down:
	docker compose -f docker-compose.dev.yml down

lint:
	$(VENV)/bin/ruff check app tests || true

format:
	$(VENV)/bin/ruff check --fix app tests
	$(VENV)/bin/ruff format app tests

ci-test:
	$(PYTEST) --cov=app --cov-report=term --cov-report=html
