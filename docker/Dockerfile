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

# =============================================================================
# Build arguments
# =============================================================================
ARG APP_VERSION=1.0.0
ARG APP_TITLE="corrupt-video-inspector"
ARG APP_DESCRIPTION="A Docker-based tool to detect and report corrupt video files using FFmpeg"
ARG APP_USER=inspector

# Create non-root user
RUN useradd -m -u 1000 ${APP_USER} && chown -R ${APP_USER}:${APP_USER} /app

# Set Python path
ENV PYTHONPATH=/app
ENV PATH="/home/${APP_USER}/.local/bin:$PATH"

# =============================================================================
# Dependencies stage - Install Python dependencies
# =============================================================================
FROM base AS dependencies

WORKDIR /app


# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel hatchling

# Install Poetry
RUN pip install poetry

# Configure Poetry to not use virtualenvs
RUN poetry config virtualenvs.create false

# Install dependencies and project with Poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the source code
COPY src/ ./src/

# =============================================================================
# Development stage - For development with mounted source code
# =============================================================================
FROM base AS development

# =============================================================================
# Build arguments
# =============================================================================
ARG APP_VERSION=1.0.0
ARG APP_TITLE="corrupt-video-inspector"
ARG APP_DESCRIPTION="A Docker-based tool to detect and report corrupt video files using FFmpeg"
ARG APP_USER=inspector

USER ${APP_USER}

# Create directories for volumes
RUN mkdir -p /app/videos /app/output /app/logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

ENTRYPOINT ["dumb-init", "--"]
CMD ["python3", "-m", "src", "--help"]

LABEL org.opencontainers.image.title=${APP_TITLE}
LABEL org.opencontainers.image.version=${APP_VERSION}
LABEL org.opencontainers.image.description=${APP_DESCRIPTION}

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
USER ${APP_USER}

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

ENTRYPOINT ["dumb-init", "--"]
CMD ["python3", "-m", "src"]

LABEL org.opencontainers.image.title=${APP_TITLE}
LABEL org.opencontainers.image.version=${APP_VERSION}
LABEL org.opencontainers.image.description=${APP_DESCRIPTION}
