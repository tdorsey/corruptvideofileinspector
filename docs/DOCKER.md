# Docker Setup Guide

This document provides comprehensive instructions for building and running the Corrupt Video Inspector with Docker, implementing security best practices.

## Docker Best Practices Implemented

### ✅ Multi-Stage Builds

Our Dockerfile uses multi-stage builds to optimize image size and security:

- **Build Stage**: Installs build tools, dependencies, and compiles the application
- **Runtime Stage**: Contains only the runtime environment and application files
- **Benefits**: 32% smaller images (922MB → 628MB), better security isolation

### ✅ Non-Root User Security

The container runs as a non-root user for enhanced security:

- **User**: `inspector` (UID 1000)
- **Benefits**: Reduced attack surface, principle of least privilege
- **Implementation**: User created during build, all files owned correctly

### ✅ Configuration File Mounting

External configuration files are mounted via Docker volumes:

- **Mount Point**: `/app/config/config.yaml`
- **Benefits**: Immutable configuration, easy updates without rebuilding
- **Security**: Read-only mounting prevents accidental modification

## Building Images

### Production Image (Multi-stage)

```bash
# Build optimized production image
docker build -f docker/Dockerfile -t corrupt-video-inspector:latest .

# Check image size
docker images corrupt-video-inspector:latest
```

### Development Image

```bash
# Build development image with additional tools
docker build -f docker/Dockerfile.dev -t corrupt-video-inspector:dev .
```

## Running Containers

### Basic Usage

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit configuration as needed
nano config.yaml

# Run container with mounted config
docker run --rm \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  corrupt-video-inspector:latest
```

### Complete Setup with Volumes

```bash
# Create output directory
mkdir -p ./output

# Run with all necessary mounts
docker run --rm \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  -v /path/to/your/videos:/app/videos:ro \
  -v $(pwd)/output:/app/output \
  corrupt-video-inspector:latest
```

### Using Docker Compose

```bash
# Start production environment
cd docker
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f video

# Stop services
docker compose down
```

### Development Environment

```bash
# Start development environment
cd docker
docker compose --profile dev up -d dev

# Connect to development container
docker exec -it video-dev /bin/bash

# Inside container, you can:
# - Edit code (mounted from host)
# - Run tests
# - Install additional packages
# - Debug the application
```

## Configuration Management

### Configuration File Structure

```yaml
# config.yaml
scanner:
  max_workers: 4
  default_mode: "hybrid"
  recursive: true
  extensions: [".mp4", ".mkv", ".avi", ".mov", ".wmv"]

ffmpeg:
  quick_timeout: 60
  deep_timeout: 900
  command: "/usr/bin/ffmpeg"

logging:
  level: "INFO"
  file: null

output:
  default_format: "json"
  pretty_print: true
```

### Environment Variables

Configuration can be overridden with environment variables:

```bash
docker run --rm \
  -e CVI_LOG_LEVEL=DEBUG \
  -e CVI_MAX_WORKERS=8 \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  corrupt-video-inspector:latest
```

### Docker Secrets (Production)

For sensitive configuration in production:

```bash
# Create secrets
echo "your_secret_value" | docker secret create trakt_token -

# Reference in docker-compose.yml
services:
  video:
    secrets:
      - trakt_token
    # Secrets available at /run/secrets/trakt_token
```

## Volume Mounting

### Required Mounts

| Mount Point | Purpose | Mode | Example |
|-------------|---------|------|---------|
| `/app/config/config.yaml` | Configuration | `ro` | `-v ./config.yaml:/app/config/config.yaml:ro` |
| `/app/videos` | Video files to scan | `ro` | `-v /media/videos:/app/videos:ro` |
| `/app/output` | Scan results | `rw` | `-v ./output:/app/output` |

### Optional Mounts

| Mount Point | Purpose | Mode | Example |
|-------------|---------|------|---------|
| `/app/logs` | Application logs | `rw` | `-v ./logs:/app/logs` |
| `/tmp` | Temporary files | `rw` | `-v /tmp:/tmp` |

## Security Considerations

### File Permissions

The container runs as UID 1000 (`inspector` user). Ensure mounted files are readable:

```bash
# Check file permissions
ls -la config.yaml

# Make readable if needed
chmod 644 config.yaml

# For directories containing videos
chmod 755 /path/to/videos
```

### Network Security

- Container doesn't expose any ports by default
- No unnecessary network access
- Can be run in isolated networks

### Read-Only Mounts

Always mount configuration and video files as read-only:

```bash
# Correct - read-only mount
-v $(pwd)/config.yaml:/app/config/config.yaml:ro

# Avoid - writable mount for config
-v $(pwd)/config.yaml:/app/config/config.yaml
```

## Troubleshooting

### Permission Denied Errors

If you encounter permission errors:

```bash
# Check file ownership
ls -la config.yaml

# Ensure files are readable by UID 1000
sudo chown 1000:1000 config.yaml
# OR
chmod 644 config.yaml
```

### Container Won't Start

```bash
# Check container logs
docker logs <container-id>

# Run with interactive shell for debugging
docker run --rm -it corrupt-video-inspector:latest /bin/bash
```

### Config File Not Found

```bash
# Verify mount is correct
docker run --rm \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  corrupt-video-inspector:latest \
  ls -la /app/config/

# Check if file exists on host
ls -la config.yaml
```

### FFmpeg Issues

```bash
# Test FFmpeg in container
docker run --rm corrupt-video-inspector:latest ffmpeg -version

# Check if video files are accessible
docker run --rm \
  -v /path/to/videos:/app/videos:ro \
  corrupt-video-inspector:latest \
  ls -la /app/videos/
```

## Performance Optimization

### Resource Limits

```bash
# Limit memory and CPU usage
docker run --rm \
  --memory=2g \
  --cpus=2 \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  corrupt-video-inspector:latest
```

### Worker Configuration

Adjust workers based on available CPU cores:

```yaml
# config.yaml
scanner:
  max_workers: 4  # Set to number of CPU cores
```

## Comparison: Single-stage vs Multi-stage

| Aspect | Single-stage | Multi-stage |
|--------|-------------|-------------|
| Image Size | 922MB | 628MB (-32%) |
| Build Time | Faster | Slightly slower |
| Security | Good | Better (isolated build) |
| Caching | Good | Excellent |
| Production Ready | Yes | Preferred |

## Migration from Legacy Setup

If migrating from the old single-stage Docker setup:

1. **Update Dockerfile references**:
   ```bash
   # Old
   docker build -t corrupt-video-inspector .
   
   # New
   docker build -f docker/Dockerfile -t corrupt-video-inspector .
   ```

2. **Update docker-compose.yml**:
   ```yaml
   # Old
   build: .
   
   # New
   build:
     context: ..
     dockerfile: docker/Dockerfile
   ```

3. **Update volume mounts**:
   ```yaml
   # Old
   - ./config.yaml:/app/config.yaml:ro
   
   # New
   - ./config.yaml:/app/config/config.yaml:ro
   ```

## Continuous Integration

For CI/CD pipelines:

```bash
# Build and test
docker build -f docker/Dockerfile -t corrupt-video-inspector:$BUILD_ID .

# Security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image corrupt-video-inspector:$BUILD_ID

# Run tests
docker run --rm corrupt-video-inspector:$BUILD_ID python -m pytest

# Push to registry
docker tag corrupt-video-inspector:$BUILD_ID your-registry/corrupt-video-inspector:$BUILD_ID
docker push your-registry/corrupt-video-inspector:$BUILD_ID
```