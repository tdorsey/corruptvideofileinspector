# ---
applyTo: "Dockerfile,docker-compose.yml,docker-compose.dev.yml,docker/entrypoint.sh,docker/secrets/*"
# ---
# Docker and Containerization Instructions

## Docker Configuration Analysis

### Dockerfile Review
1. **Base Image Selection**: Understand the container build process:
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

## Environment Variables and Configuration

### Configuration Hierarchy
Environment variables should follow this precedence (highest to lowest):
1. Runtime environment variables
2. Docker Compose environment variables
3. `.env` files
4. Application defaults

### Environment Variable Management
- **Naming Convention**: Use consistent naming (e.g., `MYAPP_DATABASE_URL`, `MYAPP_DEBUG_MODE`)
- **Sensitive Data**: Never commit secrets; use Docker secrets or external secret management
- **Environment-Specific Files**:
  - `.env.example` or `.env.template` for documentation
  - `.env.local` for local development overrides
  - `.env.test` for testing environments

### Configuration Validation
- Validate all required environment variables at application startup
- Provide clear error messages for missing or invalid configurations
- Use type conversion and validation libraries (pydantic, environs, etc.)

## Development Workflow with Docker

### Local Development Setup
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

## Best Practices


### Container Development
- **Always develop in containers** for environment consistency
- **Isolate environments** for dev, test, and prod
- **Use health checks** and proper startup ordering
- **Never commit secrets** to version control

### Configuration Management
- **Document environment variables** in `.env.example`
- **Validate configurations** across all environments
- **Update environment variable documentation** when making configuration changes

## Troubleshooting

### Common Docker Issues
- **Port conflicts**: Check for conflicting port assignments
- **Volume mounting**: Ensure proper file permissions and paths
- **Service dependencies**: Verify startup order and health checks
- **Environment variable resolution**: Check variable precedence and values

### Debugging Techniques
- **Use Compose logs**: `docker-compose logs [service]`
- **Interactive shells**: `docker-compose exec [service] bash`
- **Environment inspection**: Check environment variables inside containers
- **Network connectivity**: Test service-to-service communication
- **Health checks**: Monitor service health status

### Development Issues
- **Code changes not reflected**: Check volume mounts and file watching
- **Dependency installation**: Verify package installation in containers
- **Permission issues**: Check file ownership and container user permissions

## Security Considerations

### Container Security
- **Use non-root users** in production containers
- **Secure inter-service communication** with proper network isolation
- **Keep base images updated** and scan for vulnerabilities
- **Use multi-stage builds** to minimize attack surface

### Image Optimization
- **Use slim base images** to reduce size and attack surface
- **Multi-stage builds** for separating build and runtime dependencies
- **Layer optimization** to improve build and pull performance
- **.dockerignore**: Exclude unnecessary files from build context
