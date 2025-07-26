# =============================================================================
# Base stage - Common dependencies and setup
# =============================================================================
FROM ubuntu:22.04 AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Update system and install common dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    dumb-init \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user for security
RUN useradd -m -u 1000 inspector && \
    chown -R inspector:inspector /app

# Set Python path and user path
ENV PYTHONPATH=/app
ENV PATH="/home/inspector/.local/bin:$PATH"

# =============================================================================
# Dependencies stage - Install Python dependencies
# =============================================================================
FROM base AS dependencies

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies (with SSL workaround for CI environments)
RUN pip3 install --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    --no-cache-dir \
    --user \
    -r requirements.txt

# =============================================================================
# Development stage - Additional dev tools and setup
# =============================================================================
FROM base AS development

# Install development-specific packages
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    vim \
    nano \
    zsh \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python dependencies from dependencies stage
COPY --from=dependencies --chown=inspector:inspector /home/inspector/.local /home/inspector/.local

# Switch to non-root user
USER inspector

# Create directories for input and output
RUN mkdir -p /app/videos /app/output

# Additional development environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Use dumb-init as PID 1 for proper signal handling and process reaping
ENTRYPOINT ["dumb-init", "--"]

# Default command for development (keep container running)
CMD ["tail", "-f", "/dev/null"]

# =============================================================================
# Production stage - Minimal production image
# =============================================================================
FROM base AS production

# Copy Python dependencies from dependencies stage
COPY --from=dependencies --chown=inspector:inspector /home/inspector/.local /home/inspector/.local

# Copy the application files
COPY --chown=inspector:inspector . .

# Switch to non-root user
USER inspector

# Create directories for input and output
RUN mkdir -p /app/videos /app/output

# Production environment variables
ENV PYTHONUNBUFFERED=1

# Use dumb-init as PID 1 for proper signal handling and process reaping
ENTRYPOINT ["dumb-init", "--"]

# Default command - show help
CMD ["python3", "cli/main.py", "--help"]

# =============================================================================
# Default target
# =============================================================================
FROM production
