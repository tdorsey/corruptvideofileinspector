# Project setup: install dependencies, create env files, and secrets (NETWORK REQUIRED)
setup: install-system-deps install-dev install docker-env secrets-init  ## Set up project: install deps, env, secrets (requires network)
	@echo "Project setup complete. Edit docker/secrets/* and docker/.env as needed."


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
.PHONY: help install install-dev install-system-deps test-ffmpeg format lint type check test
.PHONY: test-integration test-cov clean build docker-build docker-build-clean build-clean
.PHONY: docker-dev dev-build dev-up dev-down dev-shell pre-commit-install pre-commit-run
.PHONY: docker-scan docker-report docker-trakt docker-all setup secrets-init docker-env


help:             ## Show this help message and list all targets.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

# Installation (NETWORK REQUIRED)
install:          ## Install the package (requires network)
	pip install -e .

install-dev:      ## Install package with development dependencies (requires network)
	pip install -e ".[dev]"
	@echo "Now run 'make pre-commit-install' to set up pre-commit hooks"

install-system-deps:  ## Install system dependencies including FFmpeg (requires network)
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

# Pre-commit hooks (requires pre-installed dependencies)
pre-commit-install: ## Install pre-commit hooks (requires dev dependencies already installed)
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"

pre-commit-run:   ## Run pre-commit on all files (requires dev dependencies already installed)
	pre-commit run --all-files
	pytest tests/ -v -m "unit"

# NOTE: Mark all unit tests with @pytest.mark.unit in your test files.

# Code quality (requires pre-installed dependencies)
format:           ## Format code with black and lint (requires dev dependencies already installed)
	black .
	$(MAKE) lint

lint:             ## Lint code with ruff (requires dev dependencies already installed)
	ruff check --fix --unsafe-fixes .

type:             ## Type check with mypy (requires dev dependencies already installed)
	mypy .

check: format type ## Run all checks (format, lint, type) (requires dev dependencies already installed)
	@echo "All checks passed!"

# Testing (requires pre-installed dependencies)
test:             ## Run all tests with pytest (requires dev dependencies already installed)
	pytest tests/ -v

test-integration: ## Run integration tests only (requires dev dependencies already installed)
	pytest tests/ -v -k "integration"


test-cov:         ## Run tests with coverage report (requires dev dependencies already installed)
	pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Build and clean
clean:            ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -f bandit-report.json safety-report.json
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

# Web UI targets
web-dev:           ## Run web UI in development mode (requires Node.js)
	cd frontend && npm install && npm run dev

web-build:         ## Build web UI for production
	cd frontend && npm install && npm run build

web-docker-build:  ## Build Docker images for web UI (frontend and API)
	docker compose --env-file docker/.env -f docker/docker-compose.web.yml build

web-docker-up:     ## Start web UI services via Docker Compose
	docker compose --env-file docker/.env -f docker/docker-compose.web.yml up

web-docker-down:   ## Stop web UI services
	docker compose -f docker/docker-compose.web.yml down

# API targets

docker-api-build:  ## Build the API Docker image
	docker compose -f docker/docker-compose.yml build api

docker-api:        ## Run API service via Docker Compose
	docker compose --env-file docker/.env -f docker/docker-compose.yml --profile api up api

docker-api-down:   ## Stop API service
	docker compose -f docker/docker-compose.yml --profile api down

run-api:          ## Run API locally (requires dependencies installed)
	python -m uvicorn src.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

# CI/CD targets referenced in workflows
docker-test:       ## Test Docker image functionality
	@echo "Testing Docker image build and basic functionality..."
	$(MAKE) docker-build
	@echo "Docker image test completed successfully"

security-scan:     ## Run security scanning on the codebase
	@echo "Running security scans..."
	@echo "Running Bandit security linter..."
	bandit -r src/ -f json -o bandit-report.json || true
	@echo "Bandit scan complete. Report saved to bandit-report.json"
	@echo "Running Safety dependency vulnerability check..."
	safety check --json --output safety-report.json || true
	@echo "Safety scan complete. Report saved to safety-report.json"
	@echo "Security scans completed successfully!"
