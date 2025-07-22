# Agent Guidelines for Corrupt Video Inspector

This is a Python-based repository for video file integrity inspection using FFmpeg. It scans directories for video files and detects corruption or playback issues. Please follow these guidelines when contributing:

## Code Standards

### Required Before Each Commit

- Run `make check` before committing any changes to ensure code quality
- This will run Black formatting, Ruff linting, and MyPy type checking
- Pre-commit hooks are available and recommended: `make pre-commit-install`

### Development Flow

- Build: `make build`
- Test: `make test`
- Full quality check: `make check` (includes format, lint, type)
- Format only: `make format`
- Lint only: `make lint`
- Type check only: `make type`

## Repository Structure

- `cli_handler.py`: Main CLI entry point and command-line interface
- `video_inspector.py`: Core video inspection logic using FFmpeg
- `utils.py`: Utility functions for file operations and helpers
- `tests/`: Integration and unit tests with test runner
- `pyproject.toml`: Modern Python packaging and tool configuration
- `Makefile`: Development commands and build automation
- `Dockerfile`: Container configuration for FFmpeg-based scanning
- `requirements.txt`: Python dependencies
- `.pre-commit-config.yaml`: Pre-commit hook configuration for code quality

## Key Guidelines

1. Follow Python best practices and PEP 8 style guidelines (enforced by Black and Ruff)
2. Maintain existing code structure and organization
3. Use type hints for function parameters and return values where practical
4. Write integration tests for new functionality in the `tests/` directory
5. Document public APIs and complex logic with clear docstrings

## AI Agent Specific Guidelines

### Before Making Changes

- Always run `make check` before committing to ensure code quality
- Use `make format` to automatically format code with Black and Ruff
- Validate changes don't break existing functionality with `make test`

### Pull Request Requirements

- Pull requests MUST NOT have conflicts, test failures, or lint errors
- Run Black and Ruff prior to every commit, fixing any errors encountered
- Ensure all tests pass before submitting changes
- Follow the existing code style and patterns in the repository

### Development Workflow

1. Make minimal, focused changes that address the specific issue
2. Format code: `make format`
3. Run full checks: `make check`
4. Test changes: `make test`
5. Commit only when all checks pass
