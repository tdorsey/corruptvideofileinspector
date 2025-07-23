.PHONY: help install install-dev format lint type check test test-integration clean build docker-build docker-run docker-dev docker-dev-build docker-dev-run pre-commit-install pre-commit-run

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
	@echo "  docker-build        Build Docker image"
	@echo "  docker-run          Run Docker container"
	@echo "  docker-dev-build    Build development Docker image"
lint:
	ruff check --fix .
	@echo "  docker-dev-run      Run development Docker container"
	@echo "  docker-dev          Start development environment with Docker Compose"

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

pre-commit-run:
	pre-commit run --all-files

# Code quality
format:
	black .
	ruff check --fix --unsafe-fixes .

type:
	mypy .

check: format lint type
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

# Docker
docker-build:
	docker build -t corrupt-video-inspector .

docker-run:
	@echo "Usage: make docker-run VIDEO_DIR=/path/to/videos"
	@if [ -z "$(VIDEO_DIR)" ]; then \
		echo "Please specify VIDEO_DIR, e.g., make docker-run VIDEO_DIR=/path/to/videos"; \
		exit 1; \
	fi
	docker run --rm \
		-v "$(VIDEO_DIR):/app/videos:ro" \
		-v "$(PWD)/output:/app/output" \
		corrupt-video-inspector \
		python3 cli_handler.py --verbose --json /app/videos

# Development Docker
docker-dev-build:
	docker build -f Dockerfile.dev -t corrupt-video-inspector-dev .

docker-dev-run:
	docker run --rm -it \
		-v "$(PWD):/app" \
		-v dev_videos:/app/videos \
		-v dev_output:/app/output \
		corrupt-video-inspector-dev \
		/bin/bash

docker-dev:
	@echo "Starting development environment..."
	docker compose --profile dev up -d dev
	@echo "Development container started. Connect with:"
	@echo "  docker exec -it video-dev /bin/bash"
	@echo "Or use VS Code with the Dev Containers extension."
	@echo ""
	@echo "To stop: docker compose --profile dev down"
