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
dev: ## Start backend + frontend (runs in foreground)
	@echo "Starting backend on :8000 and frontend on :3000..."
	@trap 'kill 0' EXIT; \
		(cd backend && uv run uvicorn app.main:app --reload --port 8000) & \
		(cd frontend && npm run dev) & \
		wait

.PHONY: backend-dev
backend-dev: ## Start backend only
	cd backend && uv run uvicorn app.main:app --reload --port 8000

.PHONY: frontend-dev
frontend-dev: ## Start frontend only
	cd frontend && npm run dev

.PHONY: test
test: ## Run all tests
	cd backend && uv run pytest -v

.PHONY: lint
lint: ## Lint backend + frontend
	cd backend && uv run ruff check .
	cd frontend && npm run lint
	cd frontend && npm run fmt:check

.PHONY: fmt
fmt: ## Format backend + frontend
	cd backend && uv run ruff check --fix . && uv run black .
	cd frontend && npm run fmt

.PHONY: precommit-install
precommit-install: ## Install git hooks
	pre-commit install
