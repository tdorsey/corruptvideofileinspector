# General Instructions

## Project Overview

A comprehensive Python CLI tool for detecting corrupted video files using FFmpeg, with optional Trakt.tv synchronization and Docker containerization support.

## Getting Started

Always reference the specialized instruction files in this directory for detailed guidance on specific topics:
- [Python Development](python.md) - Python-specific patterns and project structure
- [Configuration Management](configuration.md) - Environment variables and configuration files
- [Docker & Containerization](docker.md) - Docker builds and container workflows
- [Testing](testing.md) - Test structure and testing patterns
- [Git & Version Control](git.md) - Commit conventions and branching strategies
- [GitHub Actions & CI/CD](github-actions.md) - Workflow patterns and automation
- [Project-Specific Guidelines](project-specific.md) - Architecture and key entry points

## Quick Reference

### Essential Setup (Network Required)
```bash
sudo apt-get install -y ffmpeg    # Install FFmpeg dependency
make install-dev                  # Install all dependencies (2-5 min)
make pre-commit-install          # Setup code quality hooks
```

### Development Workflow
```bash
make check                       # Format, lint, type check (1-3 min)
make test                        # Run all tests (1-15 min)
make docker-build               # Build container (5-15 min)
```

### CLI Usage Examples
```bash
# Using installed package
corrupt-video-inspector --help
corrupt-video-inspector scan /path/to/videos --mode hybrid --output results.json

# Using without installation (requires PYTHONPATH=src)
export PYTHONPATH=$(pwd)/src
python3 cli_handler.py --config config.yaml --help
python3 cli_handler.py --config config.yaml scan --directory /path/to/videos
```

## Repository Structure

### Project Root
```
corruptvideofileinspector/
├── README.md                      # Project documentation
├── pyproject.toml                 # Python project configuration
├── Makefile                       # Development automation commands
├── .pre-commit-config.yaml        # Code quality automation
├── src/                           # Main source code
├── tests/                         # Test suite
├── docs/                          # Detailed documentation
├── docker/                        # Docker configuration
└── .github/workflows/             # CI/CD pipeline definitions
```

### Important Source Files
```
src/
├── cli/                           # Command-line interface
├── core/                          # Core business logic
├── config/                        # Configuration management
├── ffmpeg/                        # FFmpeg integration
├── output.py                      # Output formatting
├── version.py                     # Version information
└── __main__.py                    # Main entry point
```

## Working Effectively

### GitHub Copilot Agent Environment
**All required dependencies are pre-installed in the Copilot agent environment:**
- **System Dependencies**: FFmpeg and build-essential are pre-installed
- **Python Dependencies**: All dev dependencies are pre-installed
- **No Network Access Required**: Testing, linting, and formatting work without network access

### Verified Commands (Network-Independent)
```bash
make help                        # Show all available targets
make clean                       # Clean build artifacts
make check                       # Format, lint, and type check
make test                        # Run all tests
make format                      # Format code with black
make lint                        # Lint code with ruff
make type                        # Type check with mypy
make docker-env                  # Generate Docker environment files
make secrets-init                # Create Trakt secret files
```

### Prerequisites (For Local Development)
- Install system dependencies:
  ```bash
  sudo apt-get install -y ffmpeg build-essential
  ```
- Verify FFmpeg installation: `ffmpeg -version`
- Python 3.13+ is required

## Common Tasks and Commands

### Project Setup
```bash
make setup                       # Full setup: install + docker-env + secrets
make docker-env                  # Generate Docker env files (10-30 sec)
make secrets-init                # Create secret files (5-10 sec)
```

### Code Quality
```bash
make format                      # 30-60 sec
make lint                        # 10-30 sec
make type                        # 30 sec-2 min
make check                       # All above combined
make clean                       # Clean build artifacts
```

### Testing
```bash
make test                        # 1-15 min
make test-integration           # 5-15 min
pytest tests/ -v -m "unit"     # 30 sec-2 min (unit tests only)
make test-cov                   # Run with coverage
```

### Docker Workflow
```bash
make docker-build               # Build production image
make dev-build                  # Build development image
make dev-up                     # Start dev container
make dev-down                   # Stop dev container
make dev-shell                  # Interactive shell access
make docker-scan                # Run scan via Docker
```

## Critical Warnings and Timing

### Dependencies in Copilot Environment
- **Pre-installed**: All system and Python dependencies are available
- **No Network Access Required**: Testing, linting, formatting work offline
- **Local Development**: Network connectivity to PyPI required only locally

### Build and Test Timeouts
- **Testing**: Unit tests 30 sec-2 min, full suite up to 15 minutes
- **CLI Operations**: Basic commands complete in <1 second
- **Basic Scans**: Empty directory scans complete in <1 second
- **NEVER CANCEL** long-running operations - video processing takes time

## Troubleshooting Common Issues

### Development Issues (Copilot Environment)
- **Import errors**: Ensure PYTHONPATH includes src: `export PYTHONPATH=/path/to/repo/src`
- **Permission errors**: Check file/directory permissions for video processing
- **CLI configuration errors**: CLI requires a valid config.yaml file
- **Missing make targets**: `docker-test` and `security-scan` targets are available

### Local Development Issues
- **Network timeouts**: Increase pip timeout: `pip install --timeout 300`
- **SSL errors**: May indicate firewall/proxy issues - use Docker as fallback
- **Poetry conflicts**: Clear cache: `pip cache purge` and retry
- **Build system failures**: Ensure build-essential is installed
- **FFmpeg not found**: Install system package: `sudo apt-get install ffmpeg`

### Testing Failures
- **Missing test videos**: Some integration tests require actual video files
- **Timeout errors**: Video processing can be slow - use appropriate timeouts
- **Docker issues**: Ensure Docker service is running and accessible
- **Import errors in tests**: Set PYTHONPATH before running tests manually
