# Secure Configuration Module

This document describes the secure configuration module for the Corrupt Video Inspector application, which enforces strict security boundaries for sensitive data by restricting secrets to Docker's native secret management system only.

## Overview

The configuration module provides a comprehensive system for managing application settings with the following key features:

- **Security-First Design**: Sensitive values (API keys, passwords, tokens) MUST only be loaded from Docker secrets
- **Fail-Fast Behavior**: Application fails immediately if required sensitive values are missing
- **Configuration Precedence**: Clear precedence order for configuration sources
- **Type Safety**: Automatic type conversion and validation
- **Backward Compatibility**: Supports existing CVI_ environment variables

## Configuration Precedence

Configuration values are loaded in the following precedence order (lowest to highest):

1. **Configuration File** - Base configuration from YAML files
2. **CLI Flags** - Command line arguments
3. **Docker Secrets** - Sensitive values ONLY (at `/run/secrets/`)
4. **Environment Variables** - Non-sensitive configuration overrides
5. **Defaults** - Final fallback for non-sensitive values only

## Sensitive vs Non-Sensitive Values

### Sensitive Values (Docker Secrets Only)

These configuration values are classified as sensitive and MUST only be provided via Docker secrets:

- `secret_key` - Application secret key
- `api_key` - External API authentication key
- `database_password` - Database authentication password  
- `client_secret` - OAuth client secret (confidential)

**Security Enforcement:**
- Sensitive values from environment variables, CLI arguments, or YAML files are rejected
- Missing sensitive values cause the application to fail at startup
- No default/placeholder values for sensitive data

### Non-Sensitive Values (Any Source)

These values can be set via any configuration source:

- Application settings (`debug`, `host`, `port`, `log_level`)
- Database connection strings (without passwords)
- Processing configuration (`max_workers`, `default_mode`)
- File scanning settings (`recursive`, `extensions`)
- OAuth client ID (public identifier)
- OAuth redirect URL

## Usage Examples

### Basic Usage

```python
from config import SECRET_KEY, API_KEY, CLIENT_ID, HOST, PORT, DEBUG

# Direct access to configuration values
print(f"Starting application on {HOST}:{PORT}")
print(f"Debug mode: {DEBUG}")

# SECRET_KEY and API_KEY will be None if not provided via Docker secrets
if SECRET_KEY:
    print("Application secret key loaded from Docker secrets")
```

### Function-Based Access

```python
from config import get_config

# Get configuration values with defaults
client_id = get_config('client_id', 'default-client-id')
timeout = get_config('timeout', 30)

# Get sensitive values (will raise error if missing)
try:
    api_key = get_config('api_key')
    print("API key loaded successfully")
except ConfigurationError as e:
    print(f"API key missing: {e}")
```

### Adding Custom Sensitive Keys

```python
from config import add_sensitive_key, load_config

# Add custom sensitive keys before loading configuration
add_sensitive_key('custom_api_token')
add_sensitive_key('encryption_key')

# Now these keys must be provided via Docker secrets
config = load_config()
```

### Loading Configuration

```python
from config import load_config

# Load with validation (production)
config = load_config()

# Load without validation (testing)
config = load_config(validate_secrets=False)

# Load with specific file and CLI args
config = load_config(
    config_file='config.yaml',
    cli_args=['--host', '0.0.0.0', '--port', '3000']
)
```

## Docker Integration

### Docker Compose Example

```yaml
version: '3.8'
services:
  app:
    image: corrupt-video-inspector:latest
    environment:
      - APP_HOST=0.0.0.0
      - APP_PORT=8000
      - APP_DEBUG=false
      - CLIENT_ID=your-oauth-client-id
      - REDIRECT_URL=https://your-app.com/oauth/callback
    secrets:
      - secret_key
      - api_key
      - database_password
      - client_secret
    command: ["python", "app.py", "--log-level", "INFO"]

secrets:
  secret_key:
    external: true
  api_key:
    file: ./secrets/api_key.txt
  database_password:
    external: true
  client_secret:
    external: true
```

### Environment Variables

The module supports both new `APP_*` and legacy `CVI_*` environment variable prefixes:

```bash
# New format (recommended)
export APP_HOST=0.0.0.0
export APP_PORT=8000
export APP_DEBUG=true
export APP_LOG_LEVEL=INFO
export CLIENT_ID=my-oauth-client-id

# Legacy format (backward compatibility)
export CVI_LOG_LEVEL=DEBUG
export CVI_MAX_WORKERS=8
```

### CLI Arguments

```bash
python app.py \
  --host 0.0.0.0 \
  --port 3000 \
  --debug \
  --log-level INFO \
  --max-workers 8 \
  --client-id my-client \
  --config-file config.yaml
```

## Error Handling

### Missing Sensitive Values

```python
from config import ConfigurationError, load_config

try:
    config = load_config()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Example: Required sensitive configuration values are missing: 
    # secret_key, api_key. These must be provided via Docker secrets at /run/secrets/
    exit(1)
```

### Configuration Not Loaded

```python
from config import get_config

try:
    value = get_config('some_key')
except RuntimeError as e:
    print(f"Configuration not loaded: {e}")
    # Configuration must be loaded first with load_config()
```

## Security Features

### Strict Secret Enforcement

```python
# This will be REJECTED - sensitive values cannot come from environment
os.environ['APP_SECRET_KEY'] = 'should-be-rejected'

# This will be REJECTED - sensitive values cannot come from YAML
config_data = {'secret_key': 'should-be-rejected'}

# This is ACCEPTED - sensitive values from Docker secrets only
# /run/secrets/secret_key contains the actual secret
```

### Fail-Fast Validation

```python
# Application fails immediately if required secrets are missing
config = load_config()  # Raises ConfigurationError if secrets missing
```

### No Secret Exposure

```python
# Secrets are never logged, even at DEBUG level
# Error messages don't contain sensitive values
# Process lists don't show secrets (not in environment variables)
```

## Migration Guide

### From Existing Configuration

1. **Identify Sensitive Values**: Review your configuration and identify sensitive values (API keys, passwords, tokens)

2. **Move to Docker Secrets**: Create Docker secret files or external secrets for sensitive values

3. **Update Environment Variables**: Change from `CVI_*` to `APP_*` prefixes (optional, `CVI_*` still supported)

4. **Update Code**: Replace direct config access with new module imports

   ```python
   # Old
   from config import load_config
   config = load_config()
   secret = config.secrets.api_key
   
   # New
   from config import API_KEY
   # API_KEY is automatically loaded from Docker secrets
   ```

5. **Test Security**: Verify that sensitive values are rejected from non-Docker sources

## Best Practices

1. **Always Use Docker Secrets for Sensitive Data**: Never put sensitive values in environment variables, YAML files, or CLI arguments

2. **Validate Configuration Early**: Load and validate configuration at application startup

3. **Use Function-Based Access for Dynamic Values**: Use `get_config()` for values that might not always be present

4. **Fail Fast**: Don't provide fallback values for missing sensitive configuration

5. **Document Sensitive Keys**: Clearly document which configuration keys are sensitive

6. **Regular Security Audits**: Regularly review configuration usage to ensure sensitive data isn't leaking

## Troubleshooting

### Common Issues

1. **"Required sensitive configuration values are missing"**
   - Ensure Docker secrets are properly mounted
   - Check that secret files exist in `/run/secrets/`
   - Verify secret file names match expected keys

2. **"Configuration not loaded"**
   - Call `load_config()` before accessing configuration values
   - Ensure the configuration module is imported properly

3. **Environment variables not working**
   - Use `APP_*` prefix for new variables
   - Use `CVI_*` prefix for legacy compatibility
   - Check that variables are set before loading configuration

4. **Type conversion errors**
   - Environment variables are strings and need conversion
   - Use proper values: `true`/`false` for booleans, numbers for integers

### Debug Configuration Loading

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from config import load_config
config = load_config()  # Will show debug info about configuration loading
```