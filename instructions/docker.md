# Docker & Containerization

## Docker Builds, Compose Files, and Container Workflows

### Docker Overview
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: docker-compose for multi-container workflows
- **Development**: Separate development and production images
- **Testing**: Container-based testing strategies

### Docker Commands

#### Building Images
```bash
# Production image
make docker-build                # 5-15 min, timeout 30+ min
make docker-build-clean          # Build without cache, 10-20 min, timeout 45+ min
make build-clean                 # Alias for docker-build-clean

# Development image
make dev-build                   # 5-15 min, timeout 30+ min
```

#### Development Workflow
```bash
# Start development container (detached)
make dev-up

# Stop development container
make dev-down

# Interactive shell access
make dev-shell

# Build and run development container
make docker-dev
```

#### Application Workflows
```bash
# Run video scan via Docker
make docker-scan                 # Run scan via Docker Compose

# Run report generation via Docker
make docker-report               # Run report via Docker

# Run Trakt sync via Docker
make docker-trakt                # Run Trakt sync via Docker

# Run complete scan + report sequence
make docker-all                  # Run scan + report sequence
```

### Docker Configuration Files

#### Dockerfile Structure
Multi-stage builds for optimization:
1. **Base stage**: System dependencies (FFmpeg, build-essential)
2. **Dependencies stage**: Python packages
3. **Development stage**: Dev dependencies included
4. **Production stage**: Minimal runtime dependencies only

#### Docker Compose
- **Development**: `docker-compose.yml` for local development
- **Production**: Optimized for deployment scenarios
- **Services**: Application, optional database, volume mounts

### Environment Setup

#### Generate Docker Environment
```bash
# Create docker/.env with required volume paths
make docker-env                  # 10-30 sec
```

#### Initialize Secrets
```bash
# Create Trakt secret files
make secrets-init                # 5-10 sec

# Created files:
# - docker/secrets/trakt_client_id.txt
# - docker/secrets/trakt_client_secret.txt
```

### Volume Mounts
Configure volume mounts for:
- **Video directories**: Input/output video files
- **Configuration files**: Mount config.yaml
- **Logs**: Persistent logging
- **Results**: Output data persistence

Example docker-compose volume configuration:
```yaml
volumes:
  - ./videos:/videos:ro          # Read-only video input
  - ./output:/output              # Writeable output
  - ./config.yaml:/app/config.yaml:ro
  - ./logs:/logs
```

### Container Security

#### Best Practices
- **Non-root user**: Run containers as non-root when possible
- **Read-only filesystems**: Use where appropriate
- **Secrets management**: Use Docker secrets for sensitive data
- **Network isolation**: Limit container network access
- **Image scanning**: Scan images for vulnerabilities

#### Secret Mounting
```yaml
secrets:
  - trakt_client_id
  - trakt_client_secret

secrets:
  trakt_client_id:
    file: ./docker/secrets/trakt_client_id.txt
  trakt_client_secret:
    file: ./docker/secrets/trakt_client_secret.txt
```

### Development Container Features

#### Development Image Includes
- All development dependencies (black, ruff, mypy, pytest)
- Source code mounted as volume for live editing
- Shell access for debugging
- Full toolchain for testing

#### Interactive Development
```bash
# Start shell in development container
make dev-shell

# Inside container:
pytest tests/ -v                 # Run tests
make check                       # Run code quality checks
python cli_handler.py --help     # Test CLI
```

### Container-Based Testing

#### Running Tests in Containers
```bash
# Run tests via Docker
make docker-test                 # Placeholder implementation

# Run specific test suites
docker-compose run app pytest tests/unit/ -v
docker-compose run app pytest tests/integration/ -v
```

#### Test Isolation
- Each test run in fresh container environment
- No dependency on host system configuration
- Consistent test results across environments

### Multi-Stage Build Optimization

#### Stage 1: Base
```dockerfile
FROM python:3.13-slim as base
RUN apt-get update && apt-get install -y ffmpeg build-essential
```

#### Stage 2: Dependencies
```dockerfile
FROM base as dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev
```

#### Stage 3: Development
```dockerfile
FROM dependencies as development
RUN poetry install  # Includes dev dependencies
```

#### Stage 4: Production
```dockerfile
FROM dependencies as production
COPY src/ /app/src/
# Minimal runtime configuration
```

### Troubleshooting Docker Issues

#### Common Issues
- **Docker service not running**: `systemctl start docker`
- **Permission errors**: Add user to docker group or use sudo
- **Build failures**: Check network connectivity, clear cache
- **Volume mount issues**: Check paths and permissions
- **Container crashes**: Check logs with `docker logs`

#### Debugging Commands
```bash
# View container logs
docker logs <container_id>

# Inspect container
docker inspect <container_id>

# Execute command in running container
docker exec -it <container_id> bash

# View Docker system info
docker system info

# Clean up unused resources
docker system prune
```

### Docker Networking

#### Network Configuration
- Default bridge network for simple setups
- Custom networks for service isolation
- Port mapping for external access
- Network aliases for service discovery

#### Port Mapping
```yaml
ports:
  - "8000:8000"  # Map host:container ports
```

### Docker Compose Workflows

#### Service Dependencies
```yaml
services:
  app:
    depends_on:
      - db
  db:
    image: postgres:13
```

#### Health Checks
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Performance Optimization

#### Build Performance
- **Use build cache**: Layer ordering matters
- **Multi-stage builds**: Reduce final image size
- **Minimize layers**: Combine RUN commands
- **`.dockerignore`**: Exclude unnecessary files

#### Runtime Performance
- **Resource limits**: Set memory and CPU constraints
- **Volume performance**: Use delegated/cached options
- **Network optimization**: Minimize network hops

### Docker Image Management

#### Image Tagging
```bash
# Tag images appropriately
docker tag app:latest app:v1.0.0
docker tag app:latest app:dev
```

#### Image Registry
- Push to registry for deployment
- Use semantic versioning
- Maintain latest tag for current stable

### Fallback Strategy
If local pip installation fails due to network issues:
1. Use Docker development environment instead
2. Build dev image: `make dev-build`
3. Run in container: `make dev-shell`
4. All dependencies available in container

### Docker Compose Override

#### Development Override
Create `docker-compose.override.yml` for local customization:
```yaml
version: '3.8'
services:
  app:
    volumes:
      - ./local-videos:/videos
    environment:
      - DEBUG=1
```

### Container Lifecycle

#### Start/Stop
```bash
# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View running containers
docker-compose ps
```

#### Cleanup
```bash
# Remove stopped containers
docker-compose rm

# Remove volumes
docker-compose down -v

# Full cleanup
docker system prune -a --volumes
```

### Best Practices Summary
- **Use multi-stage builds** to minimize image size
- **Layer caching** for faster builds
- **Secrets management** for sensitive data
- **Volume mounts** for development and data persistence
- **Health checks** for service readiness
- **Resource limits** to prevent resource exhaustion
- **Network isolation** for security
- **Regular cleanup** to free disk space
