# ─── Configuration ────────────────────────────────────────────────────────────

COMPOSE      = docker compose
COMPOSE_TEST = docker compose -f docker-compose.test.yml
APP_SERVICE  = api
DB_SERVICE   = db
DB_USER      = postgres
DB_NAME      = bookmark_manager
UVICORN_PORT = 8002
CELERY_APP   = app.celery_app.celery_app

.DEFAULT_GOAL := help

.PHONY: help \
        up down restart logs ps \
        dev-up install run worker beat \
        migrate migration db-shell \
        test test-local \
        lint format lint-fix \
        clean

# ─── Help ─────────────────────────────────────────────────────────────────────
# Self-documenting: reads targets with ## comments and prints an aligned table.

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ─── Docker (full stack) ──────────────────────────────────────────────────────

up: ## Start all services in the background
	$(COMPOSE) up -d

down: ## Stop and remove all containers
	$(COMPOSE) down

restart: ## Restart the API container
	$(COMPOSE) restart $(APP_SERVICE)

logs: ## Tail API logs  (Ctrl-C to stop)
	$(COMPOSE) logs -f $(APP_SERVICE)

ps: ## Show running container status
	$(COMPOSE) ps

# ─── Local dev (infra in Docker, app on host) ─────────────────────────────────

dev-up: ## Start db + redis only  (for running the app locally)
	$(COMPOSE) up -d db redis

install: ## Install Python dependencies into the active virtualenv
	pip install -r requirements.txt

run: ## Run the API locally with hot reload  (requires dev-up)
	uvicorn app.main:app --reload --port $(UVICORN_PORT)

worker: ## Run the Celery worker locally
	celery -A $(CELERY_APP) worker --loglevel=info

beat: ## Run Celery beat locally
	celery -A $(CELERY_APP) beat --loglevel=info --schedule /tmp/celerybeat-schedule

# ─── Database ─────────────────────────────────────────────────────────────────

migrate: ## Apply all pending Alembic migrations
	alembic upgrade head

migration: ## Create a new migration  (usage: make migration msg="add users table")
ifndef msg
	$(error msg is required — usage: make migration msg="your description")
endif
	alembic revision --autogenerate -m "$(msg)"

db-shell: ## Open a psql shell in the db container
	$(COMPOSE) exec $(DB_SERVICE) psql -U $(DB_USER) $(DB_NAME)

# ─── Testing ──────────────────────────────────────────────────────────────────

test: ## Run the full test suite inside Docker  (isolated, no external deps)
	$(COMPOSE_TEST) run --rm test

test-local: ## Run tests on the host  (requires dev-up + migrate)
	pytest

# ─── Code quality ─────────────────────────────────────────────────────────────

lint: ## Check for lint errors  (ruff check)
	ruff check .

format: ## Format code  (ruff format)
	ruff format .

lint-fix: ## Auto-fix lint issues and format
	ruff check --fix . && ruff format .

# ─── Housekeeping ─────────────────────────────────────────────────────────────

clean: ## Remove __pycache__ directories and .pyc files
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
