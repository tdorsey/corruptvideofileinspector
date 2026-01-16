# GitHub Copilot Instructions for Corrupt Video Inspector

This repository contains a comprehensive Python CLI tool for detecting corrupted video files using FFmpeg, with optional Trakt.tv synchronization and Docker containerization support.

## Project Context

**Primary Language**: Python 3.13 with strict type checking  
**Build System**: pyproject.toml with Poetry-style configuration  
**Testing Framework**: pytest with unit/integration separation  
**Code Quality**: Black + Ruff + MyPy enforcement via `make check`  
**Containerization**: Docker with multi-stage builds and docker-compose  
**CLI Framework**: Typer with Click integration  
**Core Dependency**: FFmpeg for video analysis and corruption detection

## GitHub Copilot Usage Guidelines

### Primary Use Cases for GitHub Copilot Chat
Use GitHub Copilot Chat for these primary scenarios in this repository:

1. **Code Implementation & Refactoring**
   - Writing new Python functions with proper type annotations
   - Implementing FFmpeg integration and video processing logic
   - Creating CLI commands and handlers using Typer framework
   - Building configuration management with Pydantic models

2. **Testing & Quality Assurance**
   - Writing unit tests with pytest markers (`@pytest.mark.unit`)
   - Creating integration tests for video processing workflows
   - Debugging test failures and improving test coverage
   - Implementing test fixtures for video file scenarios

3. **Docker & Containerization**
   - Optimizing Dockerfile configurations for multi-stage builds
   - Setting up docker-compose workflows for development
   - Troubleshooting container environment issues
   - Implementing container-based testing strategies

4. **Configuration & Environment Setup**
   - Setting up environment variables and configuration files
   - Creating Pydantic configuration models
   - Managing Docker secrets and environment-specific settings
   - Troubleshooting CLI configuration issues

### Primary Use Cases for GitHub Copilot Code Review
Use GitHub Copilot Code Review for these key scenarios:

1. **Code Quality & Standards Enforcement**
   - Ensuring Black formatting, Ruff linting, and MyPy type checking compliance
   - Validating proper type annotations and Python best practices
   - Checking adherence to 79-character line length and f-string usage
   - Reviewing import organization and code structure consistency

2. **Security & Best Practices**
   - Identifying hardcoded secrets or security vulnerabilities
   - Validating proper environment variable usage
   - Ensuring container security practices are followed
   - Checking input validation and error handling patterns

3. **Testing & Documentation Coverage**
   - Verifying that changes include appropriate unit tests
   - Ensuring pytest markers are correctly applied
   - Checking for adequate documentation updates
   - Validating that public APIs have proper docstrings

4. **Architecture & Integration Compliance**
   - Ensuring changes align with existing project structure
   - Validating FFmpeg integration patterns
   - Checking Docker and containerization compatibility
   - Reviewing CLI framework usage and command structure

### Additional Documentation

For detailed development guidance beyond Copilot-specific scenarios, see:
- **[Detailed Instructions](.github/instructions/copilot-instructions.md)** - Complete development workflow documentation
- **[Python Development](.github/instructions/python.md)** - Python-specific patterns
- **[Docker & Containerization](.github/instructions/docker.md)** - Container workflows
- **[Testing](.github/instructions/testing.md)** - Test structure and patterns
## Development Standards

### Commit Standards (REQUIRED)
All commits MUST follow [Conventional Commits](https://www.conventionalcommits.org/):
- Format: `<type>[optional scope]: <description>` (description starts lowercase)
- Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
- Examples: `feat(cli): add video scan command`, `fix(config): resolve YAML parsing error`
- See [Git & Version Control](.github/instructions/git.md) for detailed guidelines

### Code Quality Standards
- **⚠️ CRITICAL: `make check` MUST pass before every commit**
- All tests must pass before submitting changes
- Follow existing code style and patterns

### Dependency Management
When adding/updating dependencies:
- Update `poetry.lock` after changes to `pyproject.toml`
- Run `poetry lock --no-update` for changed dependencies only
- Run `poetry check` to verify consistency

### Pull Request Requirements
- Resolve all merge conflicts
- Update `poetry.lock` if dependencies were modified
- Pass all CI/CD checks (tests, linting, formatting)

## Quick Reference

### Essential Commands
```bash
# Setup and installation
make install-dev                  # Install dependencies (2-5 min)
make pre-commit-install          # Setup code quality hooks
make setup                       # Full setup: install + docker-env + secrets

# Development workflow
make check                       # Format, lint, type check (1-3 min)
make test                        # Run all tests (1-15 min)
make docker-build               # Build container (5-15 min)

# CLI usage (requires config file)
corrupt-video-inspector --help
corrupt-video-inspector scan /path/to/videos --mode hybrid --output results.json
```

### Key Project Patterns

**Import Structure**: Always set `PYTHONPATH=$(pwd)/src` for local testing  
**Configuration**: CLI requires a valid `config.yaml` file  
**Testing**: Use `@pytest.mark.unit` for unit tests, separate integration tests  
**Docker**: All containers support PUID/PGID for permission management

## Working with Copilot Agent

### Pre-installed Dependencies
In Copilot environments, these are pre-installed:
- System: FFmpeg, build-essential
- Python: black, ruff, mypy, pytest, all dev dependencies

### Network-Independent Commands
```bash
make help, make clean, make check, make test
make docker-env, make secrets-init
export PYTHONPATH=src && python3 cli_handler.py --config config.yaml --help
```

### Expected Timings
- `make check`: 30-60 seconds (timeout: 5+ min)
- Unit tests: 30 sec-2 min (timeout: 10+ min)
- Full tests: 1-15 min (timeout: 30+ min)
- Docker builds: 5-15 min (timeout: 30+ min)

## Repository Structure

```
corruptvideofileinspector/
├── src/                           # Main source code
│   ├── cli/                       # Command-line interface
│   ├── core/                      # Core business logic
│   ├── config/                    # Configuration management
│   └── ffmpeg/                    # FFmpeg integration
├── tests/                         # Test suite (unit and integration)
├── docker/                        # Docker configuration and compose files
└── .github/                       # CI/CD and workflows
```

## Troubleshooting

### Common Issues
- **Import errors**: Set `export PYTHONPATH=$(pwd)/src`
- **CLI config errors**: CLI requires valid `config.yaml` (see examples above)
- **Permission errors**: Check file/directory permissions for video processing
- **FFmpeg not found**: Install with `sudo apt-get install ffmpeg`

### Network-Dependent vs Independent
**Works without network** (Copilot environment):
- `make check`, `make test`, `make clean`
- `make docker-env`, `make secrets-init`
- CLI testing with PYTHONPATH set

**Requires network** (local development):
- `make install-dev`, `make install`
- `make docker-build` (for base images)

---

📖 **For comprehensive details**, see [Complete Instructions](.github/instructions/copilot-instructions.md)
