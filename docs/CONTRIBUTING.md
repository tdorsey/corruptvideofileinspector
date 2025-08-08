# Contributing to Corrupt Video Inspector

Thank you for your interest in contributing to Corrupt Video Inspector! This document provides guidelines and setup instructions for contributors.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- FFmpeg (for video processing functionality)

### Installation

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/corruptvideofileinspector.git
   cd corruptvideofileinspector
   ```

2. **Install the package with development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Install and set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

   This will automatically run formatting, linting, and type checking before each commit to ensure code quality and consistency.

## Code Quality and Standards

This project uses several tools to maintain code quality and consistency:

### Pre-commit Hooks

The repository uses pre-commit hooks to automatically enforce code quality standards before commits. The hooks include:

- **Formatting**: Code is automatically formatted using [Black](https://black.readthedocs.io/) with a line length of 100 characters
- **Linting**: Static code analysis using [Ruff](https://docs.astral.sh/ruff/) to identify potential errors and code quality issues
- **Type Checking**: Type annotations are validated using [MyPy](https://mypy.readthedocs.io/) to catch type-related issues
- **Basic Checks**: Trailing whitespace removal, file ending fixes, YAML/TOML validation, and more

### Manual Tool Usage

You can also run these tools manually:

```bash
# Format code with Black
make format
# or
black .

# Lint code with Ruff
make lint
# or
ruff check .

# Type check with MyPy
make type
# or
mypy .

# Run all checks at once
make check

# Fix formatting and linting issues automatically
ruff check --fix .
```

### Pre-commit Commands

```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files (useful for initial setup)
pre-commit run --all-files

# Update pre-commit hook versions
pre-commit autoupdate

# Skip pre-commit hooks for a commit (use sparingly)
git commit --no-verify -m "commit message"
```

## Testing

Run the integration tests to ensure your changes don't break existing functionality:

```bash
# Run all tests
make test
# or
python3 tests/run_tests.py
```

## Code Style Guidelines

- **Line Length**: Maximum 100 characters (enforced by Black)
- **Import Organization**: Imports are automatically organized by Ruff
- **Type Hints**: Use type hints for function parameters and return values where practical
- **Docstrings**: Use clear, concise docstrings for modules, classes, and functions
- **Variable Names**: Use descriptive variable names that clearly indicate purpose

## Pull Request Requirements

### PR Title Format

All pull request titles must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification and include an issue number reference.

**Required Format:**
```
type(optional-scope): description (#issue-number)
```

**Allowed Types:**
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates, etc.

**Examples:**
- `feat: add video scanning progress bar (#123)`
- `fix: resolve FFmpeg timeout issues (#456)`
- `docs: update installation instructions (#789)`
- `refactor(scanner): improve error handling (#111)`
- `chore: update dependencies (#222)`

**Requirements:**
- Title must start with one of the allowed conventional commit types
- Subject line must start with lowercase letter
- Must reference an issue number either in the title or PR body (e.g., `#123`)
- Optional scope can be included in parentheses after the type

The PR title validation will automatically check these requirements when you create or update a pull request.

## Submitting Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code quality guidelines

3. **Ensure all checks pass:**
   ```bash
   make check
   make test
   ```

4. **Commit your changes** (pre-commit hooks will run automatically):
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push to your fork and create a pull request** with a properly formatted title:
   ```bash
   git push origin feature/your-feature-name
   ```

## Pre-commit Hook Details

The `.pre-commit-config.yaml` file configures the following hooks:

### Basic Hooks
- `trailing-whitespace`: Removes trailing whitespace
- `end-of-file-fixer`: Ensures files end with a newline
- `check-yaml`: Validates YAML file syntax
- `check-toml`: Validates TOML file syntax
- `check-added-large-files`: Prevents accidentally committing large files
- `check-merge-conflict`: Detects merge conflict markers
- `check-ast`: Validates Python AST
- `debug-statements`: Detects debug statements (pdb, etc.)

### Formatting
- **Black**: Formats Python code consistently with 100-character line length

### Linting
- **Ruff**: Fast Python linter that replaces flake8, isort, and other tools
- **Ruff-format**: Additional formatting checks

### Type Checking
- **MyPy**: Static type checker for Python with type hint validation

## Troubleshooting

### Pre-commit Issues

If pre-commit hooks fail:

1. **Check the error messages** - they usually indicate exactly what needs to be fixed
2. **Run tools manually** to see detailed output:
   ```bash
   black .
   ruff check .
   mypy .
   ```
3. **Auto-fix issues** where possible:
   ```bash
   ruff check --fix .
   ```

### Tool Configuration

All tool configurations are centralized in `pyproject.toml`:
- Black configuration under `[tool.black]`
- Ruff configuration under `[tool.ruff]`
- MyPy configuration under `[tool.mypy]`

## Automation

This repository uses several automated workflows to streamline development and issue management:

### Issue Management
- **Auto-Assignment**: Newly created issues are automatically assigned to Copilot for initial triage and automated assistance. This helps ensure no issues go unnoticed and provides immediate automated support.

### Continuous Integration
- **PR Title Validation**: Pull request titles must follow [Conventional Commits](https://www.conventionalcommits.org/) format
- **Code Quality Checks**: Automated formatting, linting, and type checking on all PRs
- **Testing**: Comprehensive test suite runs on every push and PR

## Questions or Issues?

If you have questions about contributing or encounter issues with the development setup, please:

1. Check existing [GitHub Issues](https://github.com/tdorsey/corruptvideofileinspector/issues)
2. Create a new issue with detailed information about your problem
3. Include your Python version, operating system, and any error messages

Thank you for contributing to Corrupt Video Inspector!