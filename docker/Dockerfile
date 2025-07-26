# =============================================================================
# Base stage - Common dependencies and setup
# =============================================================================
FROM python:bookworm AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

RUN <<EOF
  apt-get update
  apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    dumb-init \
    ca-certificates
  rm -rf /var/lib/apt/lists/*
  apt-get clean
EOF

RUN <<EOF
  useradd -m -u 1000 inspector
  chown -R inspector:inspector /app
EOF

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
RUN <<EOF
  pip3 install --trusted-host pypi.org \
    --trusted-host pypi.python.org \
    --trusted-host files.pythonhosted.org \
    --no-cache-dir \
    --user \
    -r requirements.txt
EOF

# =============================================================================
# Development stage - Additional dev tools and setup
# =============================================================================
FROM base AS development

RUN <<EOF
  apt-get update
  apt-get install -y \
    git \
    curl \
    wget \
    vim \
    nano \
    zsh \
    build-essential \
    python3-dev
  rm -rf /var/lib/apt/lists/*
  apt-get clean
EOF


# Switch to non-root user
USER inspector

# Create directories for input and output
RUN mkdir -p /app/videos /app/output

# Declare mount points for config, input, output, and logs
VOLUME ["/app/config.yaml", "/app/videos", "/app/output", "/app/logs"]

# Additional development environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Use dumb-init as PID 1 for proper signal handling and process reaping
ENTRYPOINT ["dumb-init", "--"]

# Default command for development (show help)
CMD ["python3", "src/main.py"]

# =============================================================================
# Production stage - Minimal production image
# =============================================================================
FROM base AS production

# Copy the application files
COPY --chown=inspector:inspector . .

# Switch to non-root user
USER inspector

# Create directories for input and output
RUN mkdir -p /app/videos /app/output

# Declare mount points for config, input, output, and logs
VOLUME ["/app/config.yaml", "/app/videos", "/app/output", "/app/logs"]

# Production environment variables
ENV PYTHONUNBUFFERED=1

# Use dumb-init as PID 1 for proper signal handling and process reaping
ENTRYPOINT ["dumb-init", "--"]

# Default command - show help
CMD ["python3", "src/main.py"]

# =============================================================================
# Application stage - Copy application code and set entry point
# =============================================================================
FROM dependencies AS application

# Copy application code
COPY src/ /app/src/

# Set entry point
ENTRYPOINT ["python3", "src/main.py"]

# =============================================================================
# Default target
# =============================================================================
FROM production
