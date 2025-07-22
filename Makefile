.PHONY: help install install-dev format lint type check test clean build docker-build docker-run

# Default target
help:
	@echo "Available targets:"
	@echo "  install      Install the package"
	@echo "  install-dev  Install package with development dependencies"
	@echo "  format       Format code with black"
	@echo "  lint         Lint code with ruff"
	@echo "  type         Type check with mypy"
	@echo "  check        Run all checks (format, lint, type)"
	@echo "  test         Run tests with pytest"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build the package"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run Docker container"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Code quality
format:
	black .
	ruff check --fix .

lint:
	ruff check .

type:
	mypy .

check: format lint type
	@echo "All checks passed!"

# Testing
test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

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