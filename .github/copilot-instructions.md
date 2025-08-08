# Corrupt Video Inspector Development Instructions

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Verified Commands (Network-Independent)
These commands have been verified to work without network access:
- `make help` - Show all available targets
- `make clean` - Clean build artifacts  
- `make docker-env` - Generate Docker environment files
- `make secrets-init` - Create Trakt secret files
- `make setup` - Complete project setup (combines install + docker-env + secrets-init)
- Basic Python module imports work with PYTHONPATH set to src/

### Prerequisites and System Setup
- Install system dependencies first:
  ```bash
  sudo apt-get update
  sudo apt-get install -y ffmpeg build-essential
  ```
- Verify FFmpeg installation: `ffmpeg -version`
- Python 3.13+ is required and should be available

### Installation and Environment Setup
- **CRITICAL**: Network connectivity to PyPI is required. If you encounter SSL certificate errors or connection timeouts, these are environment-specific network issues that prevent package installation.
- Install development dependencies:
  ```bash
  make install-dev
  ```
  - **Expected time**: 2-5 minutes. NEVER CANCEL - Set timeout to 10+ minutes.
  - **Alternative if network issues occur**: `pip install -e ".[dev]" --timeout 300 --retries 3`
  - **Fallback for network issues**: Use Docker development environment instead

### Project Setup (Works Without Network)
- **Setup project directories and secrets**:
  ```bash
  make setup
  ```
  - This runs: `make install docker-env secrets-init`
  - **Expected time**: 10-30 seconds
- **Generate Docker environment files**:
  ```bash
  make docker-env
  ```
  - Creates docker/.env with required volume paths
- **Initialize Trakt secrets** (for Trakt.tv integration):
  ```bash
  make secrets-init
  ```
  - Creates docker/secrets/trakt_client_id.txt and trakt_client_secret.txt

### Build and Development Workflow
- **Setup pre-commit hooks** (run after install-dev):
  ```bash
  make pre-commit-install
  ```
- **Format and lint code** before making changes:
  ```bash
  make check
  ```
  - **Expected time**: 30-60 seconds. NEVER CANCEL - Set timeout to 5+ minutes.
  - This runs: black formatting, ruff linting, and mypy type checking

### Testing
- **Run all tests**:
  ```bash
  make test
  ```
  - **Expected time**: 1-3 minutes for unit tests, 5-15 minutes including integration tests. NEVER CANCEL - Set timeout to 30+ minutes.
- **Run only unit tests** (faster):
  ```bash
  pytest tests/ -v -m "unit"
  ```
  - **Expected time**: 30 seconds to 2 minutes. NEVER CANCEL - Set timeout to 10+ minutes.
- **Run with coverage**:
  ```bash
  make test-cov
  ```
  - **Expected time**: 2-5 minutes. NEVER CANCEL - Set timeout to 15+ minutes.

### Docker Development (Network-Independent Alternative)
- **Build development Docker image**:
  ```bash
  make dev-build
  ```
  - **Expected time**: 5-15 minutes. NEVER CANCEL - Set timeout to 30+ minutes.
- **Run development container with shell access**:
  ```bash
  make dev-shell
  ```
- **Note**: Use Docker environment if local pip installation fails due to network issues

## Application Validation

### CLI Testing Scenarios
Always manually validate changes by running these complete scenarios:

1. **Basic CLI functionality**:
   ```bash
   corrupt-video-inspector --help
   corrupt-video-inspector scan --help
   ```

2. **Configuration generation**:
   ```bash
   corrupt-video-inspector init-config --format yaml --output test-config.yml
   cat test-config.yml  # Verify configuration was generated
   ```

3. **Video scanning workflow** (requires test video files):
   ```bash
   mkdir -p test-videos
   # Place test video files in test-videos/
   corrupt-video-inspector scan test-videos --mode quick --output results.json
   cat results.json  # Verify results were generated
   ```

4. **Docker scanning workflow**:
   ```bash
   make docker-env  # Generate environment files
   make docker-scan  # Run scan via Docker Compose
   ```

### Manual Testing Requirements
- **ALWAYS** run through at least one complete end-to-end scenario after making changes
- Test the CLI with actual video files when possible
- Verify that configuration files are properly generated and read
- Check that output formats (JSON, CSV, YAML) are properly generated

## Common Tasks and Commands

### Development Commands
```bash
# Project setup (network-independent)
make setup                          # Full setup: install + docker-env + secrets
make docker-env                     # Generate Docker env files (10-30 sec)
make secrets-init                   # Create secret files (5-10 sec)

# Install dependencies (NETWORK REQUIRED)
make install-dev                    # 2-5 min, timeout 10+ min

# Code quality and validation
make format                         # 30-60 sec, timeout 5+ min
make lint                           # 10-30 sec, timeout 5+ min  
make type                           # 30 sec-2 min, timeout 5+ min
make check                          # All above combined, timeout 10+ min
make clean                          # Clean build artifacts (5-10 sec)

# Testing
make test                           # 1-15 min, timeout 30+ min
make test-integration              # 5-15 min, timeout 30+ min
pytest tests/ -v -m "unit"        # 30 sec-2 min, timeout 10+ min

# Pre-commit
make pre-commit-install            # 10-30 sec, timeout 2+ min
make pre-commit-run                # 1-3 min, timeout 10+ min

# Docker workflow
make docker-build                  # 5-15 min, timeout 30+ min
make docker-build-clean            # Build without cache, 10-20 min, timeout 45+ min
make build-clean                   # Alias for docker-build-clean
make dev-build                     # 5-15 min, timeout 30+ min
make dev-up                        # Start dev container (detached)
make dev-down                      # Stop dev container
make dev-shell                     # Interactive shell access
make docker-dev                    # Build and run dev container
make docker-scan                   # Run scan via Docker
make docker-report                 # Run report via Docker
make docker-trakt                  # Run Trakt sync via Docker
make docker-all                    # Run scan + report sequence
```

### CI/CD Validation Commands
Always run these before committing to ensure CI will pass:
```bash
make check    # Format, lint, and type check
make test     # Run all tests
```

## Repository Structure and Key Files

### Project Root
```
corruptvideofileinspector/
├── README.md                      # Project documentation
├── pyproject.toml                 # Python project configuration and dependencies
├── Makefile                       # Development automation commands
├── .pre-commit-config.yaml        # Code quality automation
├── src/                           # Main source code
├── tests/                         # Test suite (unit and integration)
├── docs/                          # Detailed documentation by module
├── docker/                        # Docker configuration and compose files
└── .github/workflows/             # CI/CD pipeline definitions
```

### Important Source Files
```
src/
├── cli/                           # Command-line interface → docs/CLI.md
├── core/                          # Core business logic → docs/CORE.md
├── config/                        # Configuration management → docs/CONFIG.md
├── ffmpeg/                        # FFmpeg integration → docs/FFMPEG.md
├── utils/                         # Shared utilities → docs/UTILS.md
└── __main__.py                    # Main entry point: python -m src
```

### Testing Structure
```
tests/
├── unit/                          # Unit tests (mark with @pytest.mark.unit)
├── integration/                   # Integration tests
├── fixtures/                      # Test data and fixtures
└── test_*.py                      # Direct test files
```

## Critical Warnings and Timing

### Network Dependencies
- **CRITICAL**: All pip and Poetry commands require internet access to PyPI
- **SSL Certificate Issues**: May occur in restricted network environments
- **Fallback Strategy**: Use Docker development environment if pip fails

### Build and Test Timeouts
- **Installation**: 2-5 minutes typically, but can take 10+ minutes in slow networks
- **Testing**: Unit tests 30 sec-2 min, full test suite up to 15 minutes with video processing
- **Docker Builds**: 5-15 minutes for multi-stage builds
- **NEVER CANCEL** long-running operations - video processing tests take time

### File Processing Notes
- **Video Dependencies**: FFmpeg must be installed and accessible in PATH
- **Test Files**: Integration tests may require actual video files
- **File Permissions**: Ensure read/write access to test directories and output paths

## Troubleshooting Common Issues

### Installation Failures
- **Network timeouts**: Increase pip timeout: `pip install --timeout 300`
- **SSL errors**: May indicate firewall/proxy issues - use Docker as fallback
- **Poetry conflicts**: Clear cache: `pip cache purge` and retry

### Development Issues  
- **Import errors**: Ensure PYTHONPATH includes src: `export PYTHONPATH=/path/to/repo/src`
- **FFmpeg not found**: Install system package: `sudo apt-get install ffmpeg`
- **Permission errors**: Check file/directory permissions for video processing

### Testing Failures
- **Missing test videos**: Some integration tests require actual video files
- **Timeout errors**: Video processing can be slow - use appropriate timeouts
- **Docker issues**: Ensure Docker service is running and accessible

Remember: This is a video processing application that requires actual video files for complete testing. Always validate with real video scanning workflows when possible.