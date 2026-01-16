# Configuration Management

## Environment Variables, Configuration Files, and Secrets

### Configuration Overview
- **Configuration Model**: Pydantic-based configuration validation
- **Primary Format**: YAML configuration files
- **Environment Variables**: Support for environment-based overrides
- **Secrets Management**: Docker secrets for sensitive data

### Configuration Files

#### Sample Configuration
A sample configuration file is provided at `config.sample.yaml`:
```yaml
logging:
  level: INFO
  file: /tmp/inspector.log
ffmpeg:
  command: /usr/bin/ffmpeg
  quick_timeout: 30
  deep_timeout: 1800
processing:
  max_workers: 8
  default_mode: "quick"
output:
  default_json: true
  default_output_dir: /tmp/output
  default_filename: "scan_results.json"
scan:
  recursive: true
  max_workers: 8
  mode: "quick"
  default_input_dir: /tmp/videos
  extensions: [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"]
trakt:
  client_id: ""
  client_secret: ""
  include_statuses: ["healthy"]
```

#### Configuration Commands
```bash
# Generate Docker environment files
make docker-env                  # Creates docker/.env

# Initialize Trakt secrets
make secrets-init                # Creates docker/secrets/trakt_*.txt

# Setup all configuration
make setup                       # Runs install + docker-env + secrets-init
```

### Environment Variables

#### Docker Environment Setup
The `make docker-env` target generates `docker/.env` with required volume paths:
- Automatically sets up path mappings for containers
- Configures volume mounts for video directories
- Sets environment-specific variables

#### Key Environment Variables
- `PYTHONPATH`: Set to `src/` for running without full installation
- `TRAKT_CLIENT_ID`: Trakt.tv API client ID (from secrets)
- `TRAKT_CLIENT_SECRET`: Trakt.tv API client secret (from secrets)
- `FFMPEG_COMMAND`: Path to FFmpeg binary (default: `/usr/bin/ffmpeg`)

### Secrets Management

#### Docker Secrets
Sensitive data should be stored in Docker secrets:
```bash
# Initialize Trakt secrets
make secrets-init

# Created files:
# - docker/secrets/trakt_client_id.txt
# - docker/secrets/trakt_client_secret.txt
```

#### Security Best Practices
- **Never commit secrets to source code**
- Use environment variables or secrets for sensitive data
- Keep secret files out of version control (`.gitignore`)
- Rotate secrets regularly
- Use Docker secrets for containerized deployments

### Configuration Validation
- Pydantic models validate configuration on load
- Type checking ensures correct data types
- Required fields are enforced
- Default values provided where appropriate

### Configuration Loading Priority
Configuration is loaded in this order (later overrides earlier):
1. Default values in code
2. Configuration file (YAML)
3. Environment variables
4. Docker secrets (in containerized environments)

### Pydantic Configuration Models
Example configuration model structure:
```python
from pydantic import BaseModel, Field

class FFmpegConfig(BaseModel):
    command: str = Field(default="/usr/bin/ffmpeg")
    quick_timeout: int = Field(default=30, gt=0)
    deep_timeout: int = Field(default=1800, gt=0)

class Config(BaseModel):
    ffmpeg: FFmpegConfig
    logging: LoggingConfig
    processing: ProcessingConfig
    # ... other sections
```

### CLI Configuration Requirements
**CRITICAL**: The CLI requires a configuration file to operate:
- Use sample config from documentation or `config.sample.yaml`
- Create via `make docker-env && make secrets-init`
- Specify with `--config` flag: `python3 cli_handler.py --config config.yaml`

### Configuration Testing
```bash
# Test configuration loading
python3 cli_handler.py --config config.yaml show-config

# Validate FFmpeg configuration
python3 cli_handler.py --config config.yaml test-ffmpeg
```

### Docker Configuration
- Docker Compose uses environment files (`.env`)
- Secrets mounted as files in containers
- Configuration files can be mounted as volumes
- Environment variables passed through to containers

### Configuration File Locations
- **Development**: `config.yaml` (created from `config.sample.yaml`)
- **Docker**: Mounted into containers via volumes
- **Testing**: `/tmp/config.yaml` or test-specific configs

### Trakt.tv Integration Configuration
For Trakt.tv synchronization features:
1. Obtain API credentials from Trakt.tv
2. Store in Docker secrets or environment variables
3. Configure in YAML or environment:
   ```yaml
   trakt:
     client_id: "your_client_id"
     client_secret: "your_client_secret"
     include_statuses: ["healthy"]
   ```

### Configuration Troubleshooting

#### Common Issues
- **Missing config file**: CLI requires `--config` flag
- **Invalid YAML**: Check syntax with YAML validator
- **Permission errors**: Ensure read access to config files
- **Secret not found**: Run `make secrets-init` to create secret files

#### Validation
```bash
# Check if config file is valid
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Show loaded configuration
python3 cli_handler.py --config config.yaml show-config
```

### Environment-Specific Configuration

#### Development
```bash
# Setup development environment
make docker-env secrets-init
export PYTHONPATH=$(pwd)/src
```

#### Copilot Agent Environment
```bash
# All dependencies pre-installed
make docker-env secrets-init
export PYTHONPATH=/path/to/repo/src
```

#### Production (Docker)
```bash
# Build and run with Docker
make docker-build
make docker-scan  # Uses docker-compose configuration
```

### Configuration Best Practices
- **Use YAML for complex configuration**: More readable than env vars
- **Environment variables for deployment-specific values**: Paths, hosts, ports
- **Secrets for sensitive data**: API keys, passwords, tokens
- **Validate on startup**: Fail fast with clear error messages
- **Provide sensible defaults**: Minimize required configuration
- **Document all options**: Include examples and descriptions
- **Version configuration schema**: Handle backward compatibility

### Configuration Schema Changes
When modifying configuration structure:
1. Update Pydantic models first
2. Update `config.sample.yaml`
3. Update documentation
4. Provide migration path for existing configs
5. Test backward compatibility where possible
