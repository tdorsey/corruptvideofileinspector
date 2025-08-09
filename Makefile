# Project setup: install dependencies, create env files, and secrets
setup: install-system-deps install docker-env secrets-init  ## Set up project: install deps, env, secrets
	@echo "Project setup complete. Edit docker/secrets/* and docker/.env as needed."

# Install system dependencies (FFmpeg)
install-system-deps:  ## Install system dependencies including FFmpeg
	@echo "Installing system dependencies..."
	@if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update && sudo apt-get install -y ffmpeg; \
	elif command -v brew >/dev/null 2>&1; then \
		brew install ffmpeg; \
	elif command -v yum >/dev/null 2>&1; then \
		sudo yum install -y ffmpeg; \
	elif command -v dnf >/dev/null 2>&1; then \
		sudo dnf install -y ffmpeg; \
	else \
		echo "Package manager not detected. Please install FFmpeg manually."; \
		echo "Ubuntu/Debian: sudo apt-get install ffmpeg"; \
		echo "macOS: brew install ffmpeg"; \
		echo "CentOS/RHEL: sudo yum install ffmpeg"; \
		echo "Fedora: sudo dnf install ffmpeg"; \
		exit 1; \
	fi
	@echo "System dependencies installed successfully!"

# Test FFmpeg installation
test-ffmpeg:  ## Test FFmpeg installation and show version
	@echo "Testing FFmpeg installation..."
	@ffmpeg -version | head -n 1 || (echo "FFmpeg not found! Run 'make install-system-deps' first." && exit 1)
	@echo "FFmpeg is available and working!"
# Generate required secret files for project setup
secrets-init:  ## Create required secret files in docker/secrets
	@mkdir -p docker/secrets
	touch docker/secrets/trakt_client_id.txt
	touch docker/secrets/trakt_client_secret.txt
	@echo "Created docker/secrets/trakt_client_id.txt and trakt_client_secret.txt (edit with your secrets)"
# Build and run the development Docker container using Dockerfile.dev and docker-compose.dev.yml
docker-dev:  ## Build and run the development container with dev Dockerfile and Compose
	docker compose -f docker/docker-compose.dev.yml up --build

dev-build:        ## Build the development Docker image with source code mapping
	docker compose -f docker/docker-compose.dev.yml build

dev-up:           ## Start the development container with code mapping (detached)
	docker compose -f docker/docker-compose.dev.yml up --remove-orphans

dev-down:         ## Stop the development container
	docker compose -f docker/docker-compose.dev.yml down

dev-shell:        ## Open a shell in the development container
	docker compose -f docker/docker-compose.dev.yml run --rm app bash
docker-build-clean: ## Build without cache
	docker build --no-cache -f docker/Dockerfile -t cvi:$(APP_VERSION) -t cvi:latest --build-arg APP_VERSION=$(APP_VERSION) --build-arg APP_TITLE="corrupt-video-inspector" --build-arg APP_DESCRIPTION="A Docker-based tool to detect and report corrupt video files using FFmpeg" .

# Docker image version
APP_VERSION ?= 0.1.0


# Build Docker image with both version and latest tags
docker-build:  ## Build the Docker image for corrupt-video-inspector
	docker build -f docker/Dockerfile -t cvi:$(APP_VERSION) -t cvi:latest --build-arg APP_VERSION=$(APP_VERSION) --build-arg APP_TITLE="corrupt-video-inspector" --build-arg APP_DESCRIPTION="A Docker-based tool to detect and report corrupt video files using FFmpeg" .

# Build Docker image without cache, with both version and latest tags
build-clean: ## Build the Docker image without cache (extends docker-build)
	docker build -f docker/Dockerfile -t cvi:$(APP_VERSION) -t cvi:latest --build-arg APP_VERSION=$(APP_VERSION) --build-arg APP_TITLE="corrupt-video-inspector" --build-arg APP_DESCRIPTION="A Docker-based tool to detect and report corrupt video files using FFmpeg" --no-cache .
# Generate docker/.env with required variables
docker-env:  ## Generate docker/.env with required volume paths
	@mkdir -p docker
	echo "CVI_VIDEO_DIR=$(PWD)/videos" > docker/.env
	echo "CVI_OUTPUT_DIR=$(PWD)/output" >> docker/.env
	echo "CVI_LOG_DIR=$(PWD)/logs" >> docker/.env



.DEFAULT_GOAL := help
.PHONY: help install install-dev install-system-deps test-ffmpeg format lint type check test test-integration test-cov clean build \
	docker-build docker-build-clean build-clean docker-dev dev-build dev-up dev-down dev-shell \
	pre-commit-install pre-commit-run docker-scan docker-report docker-trakt docker-all \
	setup secrets-init docker-env


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
	pytest tests/ -v -m "unit"

# NOTE: Mark all unit tests with @pytest.mark.unit in your test files.

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
docker-scan: docker-env ## Run scan service via Docker Compose
	docker compose --env-file docker/.env -f docker/docker-compose.yml up scan

docker-report:    ## Run report service via Docker Compose
	docker compose -f docker/docker-compose.yml up --build report

docker-trakt: docker-env ## Run trakt sync service via Docker Compose
	docker compose --env-file docker/.env -f docker/docker-compose.yml --profile trakt up trakt

docker-all:       ## Run scan and report in sequence via Docker Compose
	docker compose -f docker/docker-compose.yml up --build scan report

# Missing targets referenced in CI
docker-test:       ## Test Docker image functionality
	@echo "Docker test target - placeholder for future implementation"
	@echo "Current workaround: Use 'make test' for Python tests or 'make docker-build' to verify build"

security-scan:     ## Run security scanning on the codebase
	@echo "Security scan target - placeholder for future implementation"
	@echo "Current workaround: Use 'make lint' for basic code quality checks"
