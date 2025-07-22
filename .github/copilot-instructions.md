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


- **Common Issues**:
   - Port conflicts, volume mounting, service dependencies, environment variable resolution.
   - Configuration and connectivity issues.
   - Code changes not reflected, dependency installation, permission issues.
- **Debugging Techniques**:
   - Use Compose logs, interactive shells, and environment inspection.
   - Check network and service health.
- **Best Practices**:
   - Always develop in containers.
   - Isolate environments for dev, test, and prod.
   - Document and validate environment variables.
   - Use health checks and proper startup ordering.
   - Never commit secrets.

---

## 10. Security and Performance

- **Dependencies**:
   - Regularly audit for vulnerabilities (e.g., `pip-audit`).
   - Keep dependencies and base images updated.
- **Code Security**:
   - Avoid hardcoding secrets.
   - Use environment variables and Docker secrets.
   - Validate all input data.
- **Container Security**:
   - Use non-root users in production.
   - Secure inter-service communication.
- **Performance**:
   - Profile before optimizing.
   - Use efficient data structures and caching.
   - Optimize Docker images with multi-stage builds and slim base images.

---

## 11. Agent-Specific Notes

- **Lint Auto-fix**: Run `make lint-fix` before manual linting.

style errors from ruff or mypy should be fixed automatically.
- **String Formatting**: Use f-strings only.
- **Respect Project Conventions**: Always follow existing patterns and configs.
- **Container Workflows**: Prefer containerized commands.
- **Document Assumptions**: Note any assumptions made during development.
- **Environment Variables**: Document new variables in `.env.example`.
- **Configuration Changes**: Validate across all environments.

---

## 12. Type Annotation Requirement

- **Always provide type annotations** for all function parameters, return types, and variable declarations where applicable.
- Ensure all code contributions follow this standard to improve readability, maintainability, and type safety.

---
- **Line Length**: Ensure all lines are ≤ 79 characters.
- **Imports**:
   - Place all imports at the top of the file, after any comments.
   - Do not include executable code before imports.
   - Sort imports alphabetically.