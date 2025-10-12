# ---
applyTo: "src/**/*.py,cli_handler.py,video_inspector.py,utils.py"
# ---
# Python Development Instructions

## Project Structure Analysis

### Initial Assessment
1. **Examine pyproject.toml**: Always start by reading the `pyproject.toml` file to understand:
   - Project metadata (name, version, description, authors)
   - Build system configuration
   - Dependencies and optional dependencies
   - Development dependencies
   - Tool configurations (pytest, black, mypy, etc.)

2. **Identify Project Layout**: Determine if the project uses:
   - **src-layout**: Code in `src/package_name/`
   - **flat-layout**: Code directly in project root
   - **namespace packages**: Multiple related packages

3. **Check for Lock Files**: Look for dependency lock files:
   - `poetry.lock` (Poetry)
   - `Pipfile.lock` (Pipenv)
   - `requirements.txt` or `requirements/*.txt`

## Dependency Management

### Poetry Setup (REQUIRED)
This project uses Poetry for dependency management and as its build backend:
- **Install Poetry**: `curl -sSL https://install.python-poetry.org | python3 -` or `pip install poetry`
- **Verify installation**: `poetry --version`
- **Check project status**: `poetry check` validates `pyproject.toml` and `poetry.lock` consistency

### Adding Dependencies (REQUIRED WORKFLOW)
**For runtime dependencies:**
1. Add to `[project.dependencies]` in `pyproject.toml` with appropriate version constraints
2. **MUST update lock file**: Run `poetry lock --no-update` to update only the new dependency
3. Install updated dependencies: `make install-dev` or `pip install -e ".[dev]"`
4. **MUST commit both `pyproject.toml` AND `poetry.lock`** together

**For development dependencies:**
1. Add to `[project.optional-dependencies.dev]` or `[tool.poetry.group.dev.dependencies]`
2. **MUST update lock file**: Run `poetry lock --no-update`
3. Install: `make install-dev`
4. **MUST commit both files together**

### Version Constraints
- Use semantic versioning constraints:
  - `>=1.0.0,<2.0.0` for semantic versioning (allows minor updates)
  - `~=1.4.0` for compatible releases (1.4.x only)
  - `^1.4.0` for Poetry-style caret (allows 1.x.x, not 2.0.0)
  - Pin exact versions (`==1.4.0`) only when necessary for critical dependencies

### Poetry Lock File Management (CRITICAL)
**MUST update `poetry.lock` when:**
- Adding new dependencies to `pyproject.toml`
- Removing dependencies from `pyproject.toml`
- Changing version constraints in `pyproject.toml`
- Updating dependencies to newer versions

**Poetry commands for lock file:**
```bash
# Update lock file for specific changed dependencies (recommended)
poetry lock --no-update

# Update all dependencies to latest compatible versions
poetry lock

# Verify consistency between pyproject.toml and poetry.lock
poetry check

# Show installed packages and dependencies
poetry show
poetry show --tree  # Show dependency tree
poetry show --outdated  # Show outdated packages
```

### Version Management
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- This project uses `poetry-dynamic-versioning` for automatic version management from git tags
- Version is dynamically generated at build time based on git tags and commits
- Do not manually update version in `pyproject.toml` (it uses placeholder "0.0.0")

## Code Quality Standards

### Type Annotation Requirement
- **Always provide type annotations** for all function parameters, return types, and variable declarations where applicable
- Ensure all code contributions follow this standard to improve readability, maintainability, and type safety

### Code Style and Standards
- **PEP 8 Compliance**: Follow Python best practices and PEP 8 style guidelines (enforced by Black and Ruff)
- **String Formatting**: Use f-strings only
- **Line Length**: Ensure all lines are ≤ 79 characters
- **Code Organization**: Maintain existing code structure and organization
- **Imports**:
  - Place all imports at the top of the file, after any comments
  - Do not include executable code before imports
  - Sort imports alphabetically

### Writing New Code
- Follow project's existing code style and patterns
- Add type hints for all new functions and methods
- Write docstrings in the project's established format (Google, NumPy, or Sphinx style)
- **Document public APIs and complex logic** with clear docstrings
- Include appropriate error handling and logging
- **Respect Project Conventions**: Always follow existing patterns and configs

### Required Checks Before Code Changes
1. **Full quality check**: Run `make check` before committing any changes - this runs Black formatting, Ruff linting, and MyPy type checking
2. **Code formatting**: Use `make format` to automatically format code with Black and Ruff
3. **Type checking**: Run `make type` for MyPy validation
4. **Linting**: Run `make lint` for Ruff linting checks
5. **Testing**: Run `make test` to ensure all tests pass

### Development Workflow Commands
- **Build**: `make build` - Build the project
- **Test**: `make test` - Run all tests (unit and integration)
- **Full quality check**: `make check` - Comprehensive check (format, lint, type)
- **Format only**: `make format` - Black and Ruff formatting
- **Lint only**: `make lint` - Ruff linting validation
- **Type check only**: `make type` - MyPy type checking
- **Pre-commit setup**: `make pre-commit-install` - Install pre-commit hooks

### Quality Standards Enforcement
- **MUST run `make check` before every commit** - ensures code quality standards
- **Pull requests MUST NOT have conflicts, test failures, or lint errors**
- **Format code with `make format` before every commit** - fixes Black and Ruff issues automatically
- **All tests must pass** - validate with `make test` before submitting changes

## Security and Performance

### Dependencies
- Regularly audit for vulnerabilities (e.g., `pip-audit`)
- Keep dependencies updated
- Validate all input data

### Code Security
- Avoid hardcoding secrets
- Use environment variables for configuration
- Validate all input data

### Performance
- Profile before optimizing
- Use efficient data structures and caching
