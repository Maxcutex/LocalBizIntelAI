PYTHON = uv

.PHONY: help install setup-dev dev lint format test test-cov test-file test-dir test-one clean pre-commit \
        db-init migrate migrate-create seed db-reset db-reapply docker-build docker-up docker-down docker-logs \
        docker-shell docker-cleanup docker-cleanup-all

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies (all extras)
	$(PYTHON) sync --all-extras

setup-dev: install ## Setup development environment
	$(PYTHON) run pre-commit install
	@echo "Backend development environment setup complete!"

dev: ## Start backend API development server
	@echo "Starting Backend API development server on http://0.0.0.0:8000 ..."
	$(PYTHON) run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

lint: ## Run all linters and static checks
	$(PYTHON) run black --check .
	$(PYTHON) run isort --check-only .
	$(PYTHON) run flake8 --max-line-length=88 --extend-ignore=E203 .
	$(PYTHON) run mypy . --hide-error-context
	$(PYTHON) run bandit -r api models services tests --format txt --skip B101,B106,B601,B603,B607,B104,B404

format: ## Format code with black and isort
	$(PYTHON) run black .
	$(PYTHON) run isort .

test: ## Run tests
	$(PYTHON) run pytest

test-cov: ## Run tests with coverage
	$(PYTHON) run pytest --cov=api --cov=models --cov=services --cov-report=term-missing --cov-report=html

test-file: ## Run tests in a specific file: make test-file FILE=tests/path/test_something.py
	@test -n "$(FILE)" || { echo "Usage: make test-file FILE=tests/..../test_x.py"; exit 1; }
	$(PYTHON) run pytest $(FILE) $(PYTEST_OPTS)

test-dir: ## Run tests in a specific folder: make test-dir DIR=tests/subfolder
	@test -n "$(DIR)" || { echo "Usage: make test-dir DIR=tests/subfolder"; exit 1; }
	$(PYTHON) run pytest $(DIR) $(PYTEST_OPTS)

test-one: ## Run a single test node (class/test): make test-one NODE=tests/x/test_y.py::TestClass::test_name
	@test -n "$(NODE)" || { echo "Usage: make test-one NODE=tests/.../test_y.py::TestClass::test_name"; exit 1; }
	$(PYTHON) run pytest $(NODE) $(PYTEST_OPTS)

clean: ## Clean up generated files
	rm -rf .pytest_cache htmlcov .coverage coverage.xml .mypy_cache
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

pre-commit: ## Run pre-commit hooks on all files
	$(PYTHON) run pre-commit run --all-files

# Database bootstrap & migrations
db-init: ## Create the configured Postgres database if it does not exist
	$(PYTHON) run python scripts/db_init.py

# Database Migrations (placeholders until Alembic is configured)
migrate: ## Apply database migrations (requires Alembic setup)
	@echo "Applying database migrations..."
	$(PYTHON) run alembic upgrade head

migrate-create: ## Create a new autogenerate migration (use MESSAGE=\"your message\")
	@if [ -n "$(MESSAGE)" ]; then \
		echo "Creating migration with message: $(MESSAGE)"; \
		$(PYTHON) run alembic revision --autogenerate -m "$(MESSAGE)"; \
	else \
		printf "Enter migration message: "; \
		read msg; \
		$(PYTHON) run alembic revision --autogenerate -m "$$msg"; \
	fi

seed: migrate ## Apply migrations and seed the database (requires scripts/seed.py)
	@echo "Seeding database..."
	$(PYTHON) run python scripts/seed.py

db-reset: ## Drop all tables and re-apply all migrations
	@echo "Resetting database (downgrade -> base, upgrade -> head)..."
	$(PYTHON) run alembic downgrade base
	$(PYTHON) run alembic upgrade head

db-reapply: ## Re-run the latest migration only
	@echo "Reapplying last migration..."
	$(PYTHON) run alembic downgrade -1
	$(PYTHON) run alembic upgrade head

# Docker commands (assumes a Dockerfile and docker-compose setup)
docker-build: ## Build backend Docker image
	docker build -t backend-api .

docker-up: ## Start services with docker-compose
	docker-compose up --build

docker-down: ## Stop services
	docker-compose down

docker-logs: ## View logs for backend-api service
	docker-compose logs -f backend-api

docker-shell: ## Get a shell inside the backend-api container
	docker-compose exec backend-api bash

docker-cleanup: ## Example cleanup command in Docker container (customize as needed)
	@echo "⚠️  WARNING: This will run a cleanup script inside the backend-api container!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	docker-compose exec backend-api $(PYTHON) run python scripts/cleanup.py

docker-cleanup-all: ## Example full database reset in Docker (customize as needed)
	@echo "⚠️  WARNING: This will reset the database and reseed data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read dummy
	docker-compose exec backend-api $(PYTHON) run alembic downgrade base
	docker-compose exec backend-api $(PYTHON) run alembic upgrade head
	docker-compose exec backend-api $(PYTHON) run python scripts/seed.py


