PYTHON ?= python

.PHONY: dev api migrate seed test lint format frontend

dev:
	docker compose up -d postgres redis
	$(PYTHON) -m app.main

api:
	$(PYTHON) -m app.main

migrate:
	alembic upgrade head

seed:
	$(PYTHON) -m app.tasks.seed

test:
	pytest

lint:
	ruff check .
	black --check .
	mypy app

format:
	black .
	ruff check --fix .

frontend:
	cd frontend && npm install && npm run dev
