# Configuration Management Instructions

## Environment Configuration

### Configuration Sources
# ---
applyTo: "src/config/**/*.py,config.yaml,docker/secrets/*.txt"
# ---
# Configuration Instructions
1. Runtime environment variables

### Environment Variable Standards

#### Naming Convention
- Use consistent naming patterns (e.g., `MYAPP_DATABASE_URL`, `MYAPP_DEBUG_MODE`)
- Use uppercase with underscores for separation
- Group related variables with common prefixes

#### Documentation Requirements
- **Always document new environment variables** in `.env.example`
- Include descriptions of what each variable does
- Specify required vs optional variables
- Provide example values where appropriate

#### Security Best Practices
- **Never commit secrets** to version control
- Use Docker secrets or external secret management for sensitive data
- Provide placeholder values in `.env.example` files
- Use environment-specific configuration files:
  - `.env.example` or `.env.template` for documentation
  - `.env.local` for local development overrides
  - `.env.test` for testing environments

### Configuration Validation

#### Startup Validation
- **Validate all required environment variables** at application startup
- Provide clear error messages for missing or invalid configurations
- Use type conversion and validation libraries (pydantic, environs, etc.)
- Fail fast if critical configuration is missing

#### Configuration Classes
- Use structured configuration classes to organize settings
- Implement validation logic within configuration classes
- Provide sensible defaults where appropriate
- Document configuration options and their effects

### Environment-Specific Configuration

#### Development Environment
- Use `.env.local` for local development overrides
- Include development-specific debugging options
- Configure logging levels appropriate for development
- Set up hot-reloading and development servers

#### Testing Environment
- Use `.env.test` for testing-specific configuration
- Configure test databases and external service mocks
- Set appropriate logging levels for test output
- Ensure tests work with minimal configuration

#### Production Environment
- Use environment variables or secure secret management
- Validate all security-related configuration
- Configure appropriate logging and monitoring
- Optimize performance-related settings

## Configuration Changes

### When Making Configuration Changes
1. **Update environment variable documentation** in `.env.example`
2. **Validate configurations** across all environments (dev, test, prod)
3. **Test configuration loading** and validation logic
4. **Update deployment documentation** if needed
5. **Verify backward compatibility** or provide migration instructions

### Configuration Migration
- Provide clear migration paths for configuration changes
- Document deprecated configuration options
- Maintain backward compatibility when possible
- Communicate breaking changes clearly in release notes

## Troubleshooting Configuration

### Common Issues
- **Environment variable conflicts**: Check variable precedence and sources
- **Missing configuration**: Verify all required variables are set
- **Type conversion errors**: Ensure proper validation and conversion
- **File permission issues**: Check access to configuration files

### Debugging Techniques
- **Log configuration loading**: Show which sources are being used
- **Environment inspection**: Print resolved configuration values (excluding secrets)
- **Validation testing**: Test configuration validation logic separately
- **Source verification**: Confirm which configuration source is taking precedence
