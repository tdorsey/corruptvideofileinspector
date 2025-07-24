# Multi-stage build for optimized Docker image
# Build stage - Install dependencies and prepare application
FROM ubuntu:22.04 AS builder

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Update system and install build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment for isolated dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies in virtual environment
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir --upgrade pip && \
    pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Install the application in the virtual environment
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --no-cache-dir -e .

# Runtime stage - Create minimal production image
FROM ubuntu:22.04 AS runtime

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    ffmpeg \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user for security
RUN useradd -m -u 1000 inspector && \
    mkdir -p /app/videos /app/output /app/config && \
    chown -R inspector:inspector /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application files from builder stage
COPY --from=builder --chown=inspector:inspector /app /app

# Set up environment for virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app

# Switch to non-root user
USER inspector

# Use dumb-init as PID 1 for proper signal handling and process reaping
ENTRYPOINT ["dumb-init", "--"]

# Default command - use our simple entrypoint for testing
CMD ["python3", "docker_entrypoint.py"]
