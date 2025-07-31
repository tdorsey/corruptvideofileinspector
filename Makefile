

.DEFAULT_GOAL := help
.PHONY: help install install-dev format lint type check test test-integration test-cov clean build \
	docker-build docker-run docker-dev-build docker-dev-run docker-prod docker-dev \
	pre-commit-install pre-commit-run docker-scan docker-report docker-all


help:             ## Show this help message and list all targets.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

# Installation
install:          ## Install the package
	pip install -e .

install-dev:      ## Install package with development dependencies
	pip install -e ".[dev]"
	@echo "Now run 'make pre-commit-install' to set up pre-commit hooks"

# Pre-commit hooks
pre-commit-install: ## Install pre-commit hooks
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"

pre-commit-run:   ## Run pre-commit on all files
	pre-commit run --all-files

# Code quality
format:           ## Format code with black and lint
	black .
	$(MAKE) lint

lint:             ## Lint code with ruff
	ruff check --fix --unsafe-fixes .

type:             ## Type check with mypy
	mypy .

check: format type ## Run all checks (format, lint, type)
	@echo "All checks passed!"

# Testing
test:             ## Run all tests with pytest
	pytest tests/ -v

test-integration: ## Run integration tests only
	pytest tests/ -v -k "integration"

test-cov:         ## Run tests with coverage report
	pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Build and clean
clean:            ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean      ## Build the package
	python -m build

# Docker Compose (compose file inside docker/ folder)
docker-scan:      ## Run scan service via Docker Compose
	docker compose -f docker/docker-compose.yml up --build scan

docker-report:    ## Run report service via Docker Compose
	docker compose -f docker/docker-compose.yml up --build report

docker-all:       ## Run scan and report in sequence via Docker Compose
	docker compose -f docker/docker-compose.yml up --build scan report
