# ---
applyTo: "**"
# ---
# Project-Specific Instructions

## Project Overview
This is the Corrupt Video Inspector project - a Python-based repository for video file integrity inspection using FFmpeg. It scans directories for video files and detects corruption or playback issues through automated analysis.

## Architecture
- **Language**: Python 3.13
- **Build System**: pyproject.toml with Poetry-style configuration
- **Containerization**: Docker with multi-stage builds and docker-compose
- **CLI Framework**: Typer with Click integration
- **Configuration**: Pydantic models with YAML/environment variable support
- **Testing**: pytest with unit and integration test separation
- **FFmpeg Integration**: Core dependency for video analysis and corruption detection

## Key Entry Points
- **`cli_handler.py`**: Main CLI entry point and command-line interface
- **`video_inspector.py`**: Core video inspection logic using FFmpeg
- **`utils.py`**: Utility functions for file operations and helpers

## Project-Specific Patterns

### Module Organization
- **src-layout**: Code is organized under `src/` directory
- **Core modules**:
  - `src/cli/` - Command-line interface handlers
  - `src/core/` - Core business logic and models
  - `src/config/` - Configuration management
  - `src/ffmpeg/` - FFmpeg integration utilities

## Repository Structure Details

### Key Files and Directories
- **`cli_handler.py`**: Main CLI entry point and command-line interface
- **`video_inspector.py`**: Core video inspection logic using FFmpeg
- **`utils.py`**: Utility functions for file operations and helpers
- **`tests/`**: Integration and unit tests with test runner
- **`pyproject.toml`**: Modern Python packaging and tool configuration
- **`Makefile`**: Development commands and build automation
- **`Dockerfile`**: Container configuration for FFmpeg-based scanning
- **`requirements.txt`**: Python dependencies
- **`.pre-commit-config.yaml`**: Pre-commit hook configuration for code quality
- **[Workflow Instructions](../instructions/workflows.md)** - Guidelines for GitHub Actions and CI/CD workflows

### Testing Structure
- **Unit tests**: Located in `tests/unit/`
- **Integration tests**: Located in `tests/integration/`
- **Test fixtures**: Located in `tests/fixtures/` with sample video files

### Configuration Management
- **Central config**: Uses Pydantic models for type-safe configuration
- **Environment integration**: Supports both YAML files and environment variables
- **Docker integration**: Environment variables configured through docker-compose

### Testing Structure
- **Unit tests**: Located in `tests/unit/`
- **Integration tests**: Located in `tests/integration/`
- **Test markers**: Uses pytest markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
- **Containerized testing**: Tests run in Docker containers for consistency

## Development Workflow

### Local Development
1. **Use Docker for development**: All development should happen in containers
2. **Hot reloading**: Source code is mounted as volumes for immediate feedback
3. **Make targets**: Use `make` commands for common tasks:
   - `make format` - Format code with black and run linting
   - `make lint` - Run ruff linting with auto-fixes
   - `make test` - Run all tests
   - `make docker-dev` - Start development container

### Code Quality
- **Type checking**: Full mypy integration with Pydantic plugin
- **Linting**: Ruff with comprehensive rule set
- **Formatting**: Black with 100-character line length
- **Import sorting**: Handled by ruff with isort compatibility

### Dependency Management
- **Runtime deps**: Defined in `[project.dependencies]`
- **Dev deps**: Defined in `[project.optional-dependencies.dev]`
- **Version constraints**: Use semantic versioning ranges
- **Container optimization**: Multi-stage builds for production

## Key Components

### CLI Interface
- **Entry point**: `cli_handler.py` serves as main entry point
- **Command structure**: Organized using Typer with subcommands
- **Error handling**: Structured error reporting with appropriate exit codes

### Video Processing
- **FFmpeg integration**: Wrapper around FFmpeg for video analysis
- **Corruption detection**: Analyzes video files for corruption indicators
- **Batch processing**: Supports processing multiple files efficiently

### Configuration System
- **Layered config**: Environment variables override YAML config
- **Validation**: Pydantic models ensure type safety and validation
- **Docker secrets**: Supports Docker secrets for sensitive configuration

## Security Considerations
- **No hardcoded secrets**: All sensitive data via environment variables
- **Container security**: Runs as non-root user in production
- **Input validation**: All file paths and inputs validated before processing

## Performance Guidelines
- **Efficient file processing**: Minimize memory usage for large video files
- **Parallel processing**: Support for concurrent video analysis
- **Container optimization**: Optimized Docker images for faster startup

## Documentation Standards
- **Docstrings**: Use Google-style docstrings for all public functions
- **Type hints**: Complete type annotations required
- **README updates**: Keep README current with functionality changes
- **Environment docs**: Document all environment variables in `.env.example`
