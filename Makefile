SHELL := /bin/bash

# Load .env into make's environment if present
ifneq (,$(wildcard .env))
include .env
export
endif

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: dev
dev: ## Start backend + gateway + frontend (runs in foreground)
	@echo "Starting backend on :8001, gateway on :8002, and frontend on :3000..."
	@trap 'kill 0' EXIT; \
		(cd backend && uv run uvicorn app.main:app --reload --port 8001) & \
		(cd gateway && uv run uvicorn app.main:app --reload --port 8002) & \
		(cd frontend && npm run dev) & \
		wait

.PHONY: backend-dev
backend-dev: ## Start backend only
	cd backend && uv run uvicorn app.main:app --reload --port 8001

.PHONY: gateway-dev
gateway-dev: ## Start gateway only
	cd gateway && uv run uvicorn app.main:app --reload --port 8002

.PHONY: frontend-dev
frontend-dev: ## Start frontend only
	cd frontend && npm run dev

.PHONY: test
test: ## Run all tests
	cd backend && uv run pytest -v
	cd gateway && uv run pytest -v

.PHONY: lint
lint: ## Lint backend + gateway + frontend
	cd backend && uv run ruff check .
	cd gateway && uv run ruff check .
	cd frontend && npm run lint
	cd frontend && npm run fmt:check

.PHONY: fmt
fmt: ## Format backend + gateway + frontend
	cd backend && uv run ruff check --fix . && uv run black .
	cd gateway && uv run ruff check --fix . && uv run black .
	cd frontend && npm run fmt

.PHONY: precommit-install
precommit-install: ## Install git hooks
	pre-commit install

# ---- Database (runs DDL directly on the Postgres container) ----

DB_CONTAINER ?= supabase-db
PG_ADMIN_USER ?= postgres

.PHONY: db-bootstrap
db-bootstrap: ## Create syntrix schema, roles, and extensions
	@echo "Bootstrapping syntrix schema on container $(DB_CONTAINER)..."
	sed \
		-e "s|:'syntrix_admin_password'|'$(SYNTRIX_ADMIN_PASSWORD)'|g" \
		-e "s|:'syntrix_app_password'|'$(SYNTRIX_APP_PASSWORD)'|g" \
		backend/db/bootstrap.sql \
	| docker exec -i $(DB_CONTAINER) psql -U $(PG_ADMIN_USER) -d postgres -v ON_ERROR_STOP=1
	@echo "Done."

.PHONY: db-teardown
db-teardown: ## DEV ONLY — drop syntrix schema and roles
	@echo "WARNING: This will destroy ALL syntrix data!"
	docker exec -i $(DB_CONTAINER) psql -U $(PG_ADMIN_USER) -d postgres -v ON_ERROR_STOP=1 < backend/db/teardown.sql
	@echo "Done."

.PHONY: db-migrate
db-migrate: ## Run Alembic upgrade head (via docker exec)
	docker exec -i $(DB_CONTAINER) psql -U $(PG_ADMIN_USER) -d postgres -v ON_ERROR_STOP=1 -c \
		"$$(cd backend && uv run alembic upgrade head --sql)"

.PHONY: db-current
db-current: ## Show current Alembic revision
	cd backend && uv run alembic current

.PHONY: db-history
db-history: ## Show Alembic migration history
	cd backend && uv run alembic history -v
