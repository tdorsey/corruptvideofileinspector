# =============================================================================
# Base stage - Common dependencies and setup
# =============================================================================
FROM python:3.11-slim-bookworm AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies including dumb-init and ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    dumb-init \
    ca-certificates \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 inspector && chown -R inspector:inspector /app

# Set Python path
ENV PYTHONPATH=/app
ENV PATH="/home/inspector/.local/bin:$PATH"

# =============================================================================
# Dependencies stage - Install Python dependencies
# =============================================================================
FROM base AS dependencies

WORKDIR /app


# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel hatchling

# Install all runtime dependencies from pyproject.toml
RUN pip install \
    typer>=0.16.0 \
    click>=8.0.0 \
    PyYAML>=6.0 \
    requests>=2.28.0 \
    piny>=1.1.0 \
    pydantic>=2.0.0 \
    trakt>=3.4.0

# Install all dev dependencies (optional, for development image)
RUN pip install \
    black>=23.0.0 \
    ruff>=0.1.0 \
    mypy>=1.0.0 \
    pytest>=7.0.0 \
    pytest-cov>=4.0.0 \
    pre-commit>=3.0.0 \
    types-requests>=2.28.0 \
    types-PyYAML>=6.0.0

# Copy project files needed for dependency resolution
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/

# Install the project and its dependencies
RUN pip install .

# =============================================================================
# Development stage - For development with mounted source code
# =============================================================================
FROM base AS development

USER inspector

# Create directories for volumes
RUN mkdir -p /app/videos /app/output /app/logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

ENTRYPOINT ["dumb-init", "--"]
CMD ["python3", "-m", "src", "--help"]

# =============================================================================
# Production stage - Complete production image
# =============================================================================
FROM base AS production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application source code (if needed)
COPY --chown=inspector:inspector src/ /app/src/

# Create directories and set ownership as root
RUN mkdir -p /app/videos /app/output /app/logs && chown -R inspector:inspector /app

# Switch to non-root user after directories are created and owned
USER inspector

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

ENTRYPOINT ["dumb-init", "--"]
CMD ["python3", "-m", "src"]
