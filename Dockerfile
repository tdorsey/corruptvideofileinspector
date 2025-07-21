# Use Ubuntu as base image for better ffmpeg support
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Update system and install dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create a non-root user for security
RUN useradd -m -u 1000 inspector && \
    chown -R inspector:inspector /app

# Copy the application files
COPY . .

# Ensure all files are owned by the inspector user
RUN chown -R inspector:inspector /app

# Switch to non-root user
USER inspector

# Create directories for input and output
RUN mkdir -p /app/videos /app/output

# Set Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python3", "CorruptVideoInspector.py", "--help"]
