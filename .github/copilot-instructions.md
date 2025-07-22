# GitHub Copilot Instructions for pyproject.toml-based Python Projects

## Overview
When working with Python projects that use `pyproject.toml` for configuration and Docker/Docker Compose for containerization, follow these comprehensive guidelines to ensure proper project structure, dependency management, containerized development practices, and environment configuration.

## Project Structure Analysis

### Initial Assessment
1. **Examine pyproject.toml**: Always start by reading the `pyproject.toml` file to understand:
   - Project metadata (name, version, description, authors)
   - Build system configuration
   - Dependencies and optional dependencies
   - Development dependencies
   - Tool configurations (pytest, black, mypy, etc.)

2. **Analyze Docker Configuration**: Review containerization setup:
   - `Dockerfile` or multi-stage `Dockerfile`
   - `docker-compose.yml` and any override files (`docker-compose.override.yml`, `docker-compose.dev.yml`)
   - `.dockerignore` file contents
   - Environment variable definitions and usage

3. **Environment Configuration**: Identify configuration sources:
   - `.env` files (`.env`, `.env.local`, `.env.development`, etc.)
   - Environment variables in docker-compose files
   - ConfigMaps or secrets if using orchestration platforms
   - Settings modules or configuration classes in code

4. **Identify Project Layout**: Determine if the project uses:
   - **src-layout**: Code in `src/package_name/`
   - **flat-layout**: Code directly in project root
   - **namespace packages**: Multiple related packages

3. **Check for Lock Files**: Look for dependency lock files:
   - `poetry.lock` (Poetry)
   - `Pipfile.lock` (Pipenv)
   - `requirements.txt` or `requirements/*.txt`

## Docker and Containerization

### Docker Configuration Analysis
1. **Dockerfile Review**: Understand the container build process:
   - Base image selection and rationale
   - Multi-stage builds for optimization
   - Python version consistency with pyproject.toml
   - Package installation method (pip, poetry, etc.)
   - Working directory and file copying patterns
   - User permissions and security considerations

2. **Docker Compose Structure**: Analyze service definitions:
   - Service dependencies and startup order
   - Volume mounts (code, data, logs)
   - Network configurations
   - Port mappings
   - Health checks and restart policies

### Environment Variables and Configuration

#### Configuration Hierarchy
Environment variables should follow this precedence (highest to lowest):
1. Runtime environment variables
2. Docker Compose environment variables
3. `.env` files
4. Application defaults

#### Environment Variable Management
- **Naming Convention**: Use consistent naming (e.g., `MYAPP_DATABASE_URL`, `MYAPP_DEBUG_MODE`)
- **Sensitive Data**: Never commit secrets; use Docker secrets or external secret management
- **Environment-Specific Files**: 
  - `.env.example` or `.env.template` for documentation
  - `.env.local` for local development overrides
  - `.env.test` for testing environments

#### Configuration Validation
- Validate all required environment variables at application startup
- Provide clear error messages for missing or invalid configurations
- Use type conversion and validation libraries (pydantic, environs, etc.)

### Development Workflow with Docker

#### Local Development Setup
1. **Development Environment**: Use docker-compose for consistent development:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
   ```

2. **Volume Mounting**: Ensure code changes reflect immediately:
   - Mount source code as volumes for hot-reloading
   - Use bind mounts for development dependencies
   - Separate data volumes for persistence

3. **Development Dependencies**: Install development tools in development containers:
   - Testing frameworks
   - Linters and formatters
   - Debugging tools
   - Development servers with auto-reload

## Dependency Management

### Adding Dependencies
- For runtime dependencies: Add to `[project.dependencies]` or use tool-specific commands
- For development dependencies: Add to `[project.optional-dependencies.dev]` or tool-specific dev groups
- Always specify appropriate version constraints:
  - `>=1.0.0,<2.0.0` for semantic versioning
  - `~=1.4.0` for compatible releases
  - Pin exact versions only when necessary

### Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml` consistently
- Consider using dynamic versioning with tools like `setuptools_scm`

## Code Quality and Testing

### Required Checks Before Code Changes
1. **Run existing tests**: Use containerized testing environment
   ```bash
   docker-compose run --rm app python -m pytest
   ```
2. **Check code formatting**: Use containerized tools or ensure consistency
3. **Type checking**: Run mypy in container if configured
4. **Linting**: Run configured linters in containerized environment
5. **Environment validation**: Verify all required environment variables are documented and validated

### Writing New Code
- Follow project's existing code style and patterns
- Add type hints for all new functions and methods
- Write docstrings in the project's established format (Google, NumPy, or Sphinx style)
- Include appropriate error handling and logging
- **Configuration Changes**: Update environment variable documentation and validation
- **Docker Changes**: Test container builds locally before committing

### Testing Requirements
- Write unit tests for all new functionality
- Maintain or improve test coverage
- Use project's testing framework (pytest, unittest, etc.)
- Follow existing test file naming conventions
- Add integration tests for complex features
- **Containerized Testing**: Ensure tests work in Docker environment
- **Environment Testing**: Test with different environment variable configurations
- **Database/Service Testing**: Use Docker Compose for integration tests with databases, message queues, etc.

## Build and Packaging

### Build System Compatibility
- Respect the configured build backend (`setuptools`, `poetry-core`, `hatchling`, etc.)
- Use appropriate build commands:
  - `python -m build` for PEP 517 compliant builds
  - Tool-specific commands (`poetry build`, `hatch build`, etc.)

### Package Structure
- Ensure `__init__.py` files are present where needed
- Maintain consistent import paths
- Follow package naming conventions (lowercase, underscores for separation)

## Tool Configuration

### Respect Existing Tool Configs
Always check for and respect configurations in `pyproject.toml` for:

```toml
[tool.pytest.ini_options]
[tool.mypy]
[tool.black]
[tool.ruff]
[tool.coverage.run]
[tool.setuptools]
[tool.poetry]
```

### Environment Management
- **Container Environments**: Use Docker for consistent Python environments
- Respect `.python-version` files (pyenv) in Dockerfile
- Follow project's Python version requirements from `pyproject.toml` and Dockerfile
- **Environment Variable Management**:
  - Use docker-compose environment files
  - Maintain environment variable documentation
  - Test configuration changes across different environments
- **Service Dependencies**: Ensure proper service startup order and health checks

## Documentation

### Code Documentation
- Update docstrings when modifying functions/classes
- Follow the project's docstring style (check existing code)
- Include type information in docstrings if not using type hints

### Project Documentation
- Update README.md for significant changes
- Update CHANGELOG.md if present
- Maintain API documentation consistency

## Git and Version Control

### Commit Practices
- Make atomic commits with clear messages
- Follow conventional commit format if used by project
- Don't commit generated files (build artifacts, `__pycache__`, etc.)

### Branch Management
- Create feature branches from main/master
- Keep branches focused on single features/fixes
- Rebase or merge according to project preferences

## Development Workflow

### Before Making Changes
1. **Environment Setup**:
   ```bash
   # Start development environment
   docker-compose up -d
   
   # Or build and start fresh
   docker-compose up --build
   ```
2. **Verify Services**: Ensure all required services (database, redis, etc.) are running
3. **Run Tests**: Execute test suite in containerized environment
4. **Environment Validation**: Verify all environment variables are properly configured

### During Development
1. Follow TDD practices when appropriate
2. **Hot Reloading**: Leverage volume mounts for immediate code changes
3. **Service Integration**: Test interactions with dependent services
4. Use pre-commit hooks if configured (can run in containers)
5. **Configuration Testing**: Verify changes work with different environment configurations

### Before Committing
1. **Container Testing**: Run full test suite in clean container
2. **Multi-environment Testing**: Test with different environment variable configurations
3. **Docker Build**: Verify Docker image builds successfully
4. **Service Integration**: Test with all dependent services
5. Check code formatting and linting (containerized tools)
6. Verify all new code has appropriate tests
7. **Environment Documentation**: Update environment variable documentation
8. **Configuration Changes**: Update `.env.example` if new variables added

## Common Commands Reference

### Docker Development
```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Execute commands in running container
docker-compose exec app bash
docker-compose exec app python -m pytest

# Run one-off commands
docker-compose run --rm app python manage.py migrate
docker-compose run --rm app python -m pytest

# Rebuild services
docker-compose up --build

# Stop and remove containers
docker-compose down

# Clean up (remove volumes)
docker-compose down -v
```

### Environment Management
```bash
# Load specific environment file
docker-compose --env-file .env.development up

# Override compose file
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# View effective configuration
docker-compose config

# Validate environment variables
docker-compose run --rm app python -c "import os; print(os.environ)"
```

### Installation
```bash
# Development with Docker
docker-compose run --rm app pip install -e .

# Poetry projects in Docker
docker-compose run --rm app poetry install

# Install new dependencies
docker-compose run --rm app poetry add package_name
docker-compose up --build  # Rebuild to include new dependencies
```

### Testing
```bash
# Containerized testing
docker-compose run --rm app python -m pytest

# With coverage
docker-compose run --rm app python -m pytest --cov=src

# Integration tests with services
docker-compose run --rm app python -m pytest tests/integration/

# Test specific environment
docker-compose --env-file .env.test run --rm app python -m pytest
```

### Code Quality
```bash
# Formatting in container
docker-compose run --rm app python -m black .
docker-compose run --rm app python -m ruff format .

# Linting in container
docker-compose run --rm app python -m ruff check .
docker-compose run --rm app python -m flake8 .

# Type checking in container
docker-compose run --rm app python -m mypy src/
```

### Building
```bash
# Build Docker image
docker build -t myapp:latest .

# Multi-stage build
docker build --target development -t myapp:dev .

# Build with docker-compose
docker-compose build

# Standard Python build in container
docker-compose run --rm app python -m build
```

## Error Handling and Troubleshooting

### Common Issues
1. **Container Issues**:
   - Port conflicts: Check for running services on same ports
   - Volume mounting problems: Verify paths and permissions
   - Service dependencies: Check startup order and health checks
   - Environment variable resolution: Verify variable precedence and loading

2. **Configuration Issues**:
   - Missing environment variables: Check .env files and docker-compose configuration
   - Service connectivity: Verify network configuration and service names
   - Database connection failures: Check database service startup and credentials

3. **Development Issues**:
   - Code changes not reflected: Verify volume mounts for hot-reloading
   - Dependency installation: Rebuild containers after adding dependencies
   - Permission issues: Check user mapping between host and container

### Debugging Techniques
```bash
# Debug container startup
docker-compose logs service_name

# Interactive debugging
docker-compose run --rm app bash

# Check environment variables in container
docker-compose run --rm app env

# Network debugging
docker network ls
docker-compose exec app ping database

# Service health checking
docker-compose ps
docker-compose exec app curl http://localhost:8000/health
```

### Best Practices
- **Containerized Development**: Always work within Docker containers for consistency
- **Environment Isolation**: Use separate environments for development, testing, and production
- **Configuration Management**: Keep environment variables documented and validated
- **Service Dependencies**: Use health checks and proper startup ordering
- **Security**: Never commit secrets; use proper secret management
- **Resource Management**: Monitor container resource usage and optimize as needed

## Security Considerations

### Dependencies
- Regularly audit dependencies for security vulnerabilities
- Use `pip-audit` or similar tools in containers
- Keep dependencies updated within version constraints
- **Container Security**: Regularly update base images and scan for vulnerabilities

### Code Security
- Avoid hardcoding secrets or credentials
- Use environment variables and Docker secrets for sensitive configuration
- Validate input data appropriately
- Follow secure coding practices
- **Container Security**: Use non-root users in production containers

### Environment Security
- Use Docker secrets for sensitive environment variables in production
- Implement proper network segmentation
- Secure inter-service communication
- Regular security audits of container configurations

## Performance

### Optimization Guidelines
- Profile code before optimizing
- Use appropriate data structures
- Consider memory usage for large datasets
- Implement caching where beneficial
- Monitor dependency bloat
- **Container Optimization**:
  - Use multi-stage builds to reduce image size
  - Optimize layer caching in Dockerfile
  - Monitor container resource usage
  - Use appropriate base images (slim, alpine when suitable)

---

## Notes for AI Agents

- Always respect existing project conventions over general best practices
- When in doubt, examine similar files in the project for patterns
- **Docker Considerations**: Always test changes in containerized environment
- **Environment Variables**: Document all new environment variables in `.env.example`
- **Service Dependencies**: Consider impact on dependent services when making changes
- **Configuration Changes**: Validate that configuration changes work across all environments
- Ask clarifying questions about project-specific requirements
- Prioritize backwards compatibility unless explicitly told otherwise
- Document any assumptions made during development
- **Container Workflows**: Prefer containerized commands over local development tools
- **Linting and Formatting**: Use project-specific configurations for tools like `ruff`, `black`, etc. Follow suggestions and best practices for code quality, but always check against existing project configurations.