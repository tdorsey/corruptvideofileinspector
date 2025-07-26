# =============================================================================
# Base stage - Common dependencies and setup
# =============================================================================
FROM python:3.11-slim-bookworm AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN <<EOF
  apt-get update
  apt-get install -y \
    ffmpeg \
    dumb-init \
    ca-certificates \
    --no-install-recommends
  rm -rf /var/lib/apt/lists/*
  apt-get clean
EOF

# Create non-root user
RUN useradd -m -u 1000 inspector && chown -R inspector:inspector /app

# Set Python path
ENV PYTHONPATH=/app
ENV PATH="/home/inspector/.local/bin:$PATH"

# =============================================================================
# Dependencies stage - Install Python dependencies
# =============================================================================
FROM base AS dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Development stage - For development with mounted source code
# =============================================================================
FROM base AS development

# Copy Python packages from dependencies stage
COPY --from=dependencies /root/.local /home/inspector/.local

# Switch to non-root user
USER inspector

# Create directories for volumes
RUN mkdir -p /app/videos /app/output /app/logs

# Development environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Ensure we're in the right directory
WORKDIR /app

# Use dumb-init as PID 1 for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Default command for development
CMD ["python3", "-m", "src.main", "--help"]

# =============================================================================
# Production stage - Complete production image
# =============================================================================
FROM base AS production

# Copy Python packages from dependencies stage
COPY --from=dependencies /root/.local /home/inspector/.local

# Copy application source code
COPY --chown=inspector:inspector src/ /app/src/

# Switch to non-root user
USER inspector

# Create directories for volumes
RUN mkdir -p /app/videos /app/output /app/logs

# Production environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Change working directory to /app so python -m src.main works
WORKDIR /app

# Use dumb-init as PID 1 for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Default command
CMD ["python3", "-m", "src.main"]
