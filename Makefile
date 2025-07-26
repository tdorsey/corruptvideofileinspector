.PHONY: help install install-dev format lint type check test test-integration clean build \
        docker-build docker-run docker-dev-build docker-dev-run docker-prod docker-dev \
        pre-commit-install pre-commit-run

help:
	@echo "Available targets:"
	@echo "  install             Install the package"
	@echo "  install-dev         Install package with development dependencies"
	@echo "  pre-commit-install  Install pre-commit hooks"
	@echo "  pre-commit-run      Run pre-commit on all files"
	@echo "  format              Format code with black"
	@echo "  lint                Lint code with ruff"
	@echo "  type                Type check with mypy"
	@echo "  check               Run all checks (format, lint, type)"
	@echo "  test                Run all tests with pytest"
	@echo "  test-integration    Run integration tests only"
	@echo "  test-cov            Run tests with coverage report"
	@echo "  clean               Clean build artifacts"
	@echo "  build               Build the package"
	@echo "  docker         Start production Docker Compose service"
	@echo "  docker-dev          Start development Docker Compose service"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	@echo "Now run 'make pre-commit-install' to set up pre-commit hooks"

# Pre-commit hooks
pre-commit-install:
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"


# Code quality
format:
	black .
	$(MAKE) lint

lint:
	ruff check --fix --unsafe-fixes .

type:
	mypy .

check: format type
	@echo "All checks passed!"

# Testing
test:
	pytest tests/ -v

test-integration:
	pytest tests/ -v -k "integration"

test-cov:
	pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Build and clean
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build



# Docker Compose (compose file inside docker/ folder)
docker:
	docker compose -f docker/docker-compose.yml up --build video
