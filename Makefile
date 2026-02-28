.PHONY: help install install-dev run test lint ci docker-build docker-run docker-dev docker-stop docker-test clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install dev dependencies
	pip install -r requirements-dev.txt

run: ## Run the app locally
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test: ## Run tests with coverage
	pytest tests/ -v --cov=app --cov-report=term-missing

lint: ## Run linting on project code
	flake8 app/ tests/

ci: lint test ## Run full CI pipeline locally

docker-build: ## Build Docker image
	docker build -t code-quality-gate .

docker-run: ## Run with Docker Compose (production)
	docker-compose up -d api

docker-dev: ## Run with Docker Compose (dev mode with hot reload)
	docker-compose up api-dev

docker-stop: ## Stop Docker containers
	docker-compose down

docker-test: ## Run tests inside Docker
	docker-compose run --rm api pytest tests/ -v --cov=app --cov-report=term-missing

clean: ## Clean temp files, caches, build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage reports/
