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

2. **Install Poetry (if not already installed):**
   ```bash
   # Via official installer (recommended)
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Or via pip
   pip install poetry
   
   # Verify installation
   poetry --version
   ```

3. **Install system dependencies (including FFmpeg):**
   ```bash
   make install-system-deps
   ```

4. **Install the package with development dependencies:**
   ```bash
   make install-dev
   ```

5. **Verify Poetry lock file consistency:**
   ```bash
   poetry check
   ```

6. **Install and set up pre-commit hooks:**
   ```bash
   make pre-commit-install
   ```

7. **Verify FFmpeg installation:**
   ```bash
   make test-ffmpeg
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

# Run specific test file
pytest tests/integration/test_database_integration.py -v

# Run specific test
pytest tests/integration/test_database_integration.py::test_scan_stores_results_in_database -v

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run database tests only
pytest tests/integration/test_database*.py -v
```

### Database Testing Guidelines

When making changes to database-related code, follow these testing practices:

#### 1. Use Temporary Databases

Always use temporary databases in tests to avoid affecting real data:

```python
import tempfile
from pathlib import Path
from src.database.service import DatabaseService

def test_my_feature():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db_service = DatabaseService(db_path)
        # Your test code here
```

#### 2. Test Database Integration

Test the full integration flow from scan to storage:

```python
def test_scan_stores_in_database(temp_db, test_video_dir):
    """Test that scan results are stored in database."""
    # Run scan
    summary, results = run_scan(test_video_dir, database_path=temp_db)
    
    # Verify database storage
    db = DatabaseService(temp_db)
    scans = db.get_recent_scans(limit=1)
    assert len(scans) == 1
    
    # Verify results
    stored_results = db.get_scan_results(scans[0].id)
    assert len(stored_results) == len(results)
```

#### 3. Test Error Handling

Ensure database operations handle errors gracefully:

```python
def test_database_error_handling():
    """Test that database errors don't crash the application."""
    # Test with invalid path
    with pytest.raises(DatabaseError):
        db = DatabaseService("/invalid/path/db.sqlite")
        db.store_scan(...)
```

#### 4. Test Query Methods

Verify all database query methods return correct results:

```python
def test_query_filters(sample_db):
    """Test query filtering by various criteria."""
    db = DatabaseService(sample_db)
    
    # Test corrupt filter
    corrupt = db.query_results(is_corrupt=True)
    assert all(r.is_corrupt for r in corrupt)
    
    # Test confidence filter
    high_conf = db.query_results(min_confidence=0.8)
    assert all(r.confidence >= 0.8 for r in high_conf)
```

#### 5. Test Data Integrity

Ensure database maintains referential integrity:

```python
def test_foreign_key_constraints(temp_db):
    """Test that foreign key constraints are enforced."""
    db = DatabaseService(temp_db)
    
    # Store scan and results
    scan_id = db.store_scan(summary)
    db.store_scan_results(scan_id, results)
    
    # Delete scan should cascade to results
    db.delete_scan(scan_id)
    remaining = db.get_scan_results(scan_id)
    assert len(remaining) == 0
```

#### 6. Test Cleanup Operations

Verify cleanup operations work correctly:

```python
def test_cleanup_old_scans(temp_db):
    """Test cleanup removes old scans correctly."""
    db = DatabaseService(temp_db)
    
    # Create old and recent scans
    # ... setup code ...
    
    # Run cleanup
    removed = db.cleanup_old_scans(days=30)
    
    # Verify only old scans removed
    remaining = db.get_recent_scans(limit=100)
    assert all(scan.age_days < 30 for scan in remaining)
```

#### 7. Integration Test Coverage

The project includes comprehensive integration tests in `tests/integration/test_database_integration.py`:

- `test_scan_stores_results_in_database`: Verify scan-to-database pipeline
- `test_incremental_scan_skips_healthy_files`: Test incremental scanning logic
- `test_report_from_database_scan`: Test report generation
- `test_database_cleanup`: Test cleanup and vacuum operations
- `test_query_with_filters`: Test advanced querying
- `test_trakt_sync_from_database`: Test Trakt integration
- `test_backup_and_restore`: Test backup/restore workflow
- `test_export_formats`: Test export to JSON/CSV/YAML

Run these tests before submitting database-related changes:

```bash
pytest tests/integration/test_database_integration.py -v
```

#### 8. Performance Testing

For large-scale operations, consider performance:

```python
import time

def test_large_scan_performance(temp_db):
    """Test database performance with large datasets."""
    db = DatabaseService(temp_db)
    
    # Generate 10,000 sample results
    results = [create_sample_result(i) for i in range(10000)]
    
    start = time.time()
    db.store_scan_results(scan_id, results)
    duration = time.time() - start
    
    # Should complete in reasonable time
    assert duration < 5.0, f"Bulk insert too slow: {duration}s"
```

#### 9. Fixtures for Testing

Use pytest fixtures for common test setup:

```python
@pytest.fixture
def temp_db():
    """Provide temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield db_path

@pytest.fixture
def sample_scan_summary():
    """Provide sample scan summary."""
    return ScanSummary(
        directory="/test/videos",
        total_files=10,
        corrupt_files=2,
        # ... other fields ...
    )
```

## Dependency Management

This project uses Poetry for dependency management and build system configuration.

### Adding or Updating Dependencies

**REQUIRED: Always update `poetry.lock` when modifying dependencies**

1. **Add dependency to `pyproject.toml`:**
   - Runtime dependencies: Add to `[project.dependencies]`
   - Development dependencies: Add to `[project.optional-dependencies.dev]` or `[tool.poetry.group.dev.dependencies]`

2. **Update the lock file (REQUIRED):**
   ```bash
   # Update only the changed dependency (recommended)
   poetry lock --no-update
   
   # Or update all dependencies to latest compatible versions
   poetry lock
   ```

3. **Verify consistency:**
   ```bash
   poetry check
   ```

4. **Install updated dependencies:**
   ```bash
   make install-dev
   ```

5. **Commit both files together:**
   ```bash
   git add pyproject.toml poetry.lock
   git commit -m "build(deps): add/update package-name"
   ```

### Useful Poetry Commands

```bash
# Check if pyproject.toml and poetry.lock are in sync
poetry check

# Show installed packages
poetry show

# Show dependency tree
poetry show --tree

# Show outdated packages
poetry show --outdated

# Update a specific package
poetry update package-name

# Update all packages to latest compatible versions
poetry update
```

## Code Style Guidelines

- **Line Length**: Maximum 100 characters (enforced by Black)
- **Import Organization**: Imports are automatically organized by Ruff
- **Type Hints**: Use type hints for function parameters and return values where practical
- **Docstrings**: Use clear, concise docstrings for modules, classes, and functions
- **Variable Names**: Use descriptive variable names that clearly indicate purpose

## Pull Request Requirements

### Critical Requirements (MUST BE MET)

Before submitting a pull request, ensure:

1. **✅ No Merge Conflicts**: All merge conflicts with the target branch MUST be resolved
2. **✅ Poetry Lock Updated**: If dependencies changed, `poetry.lock` MUST be updated and committed
3. **✅ All Tests Pass**: Run `make test` and ensure all tests succeed
4. **✅ Code Quality Checks Pass**: Run `make check` to validate formatting, linting, and type checking
5. **✅ Pre-commit Hooks Pass**: The `check-merge-conflict` hook will block commits with conflict markers

**Pull requests that do not meet these requirements will be rejected.**

### Resolving Merge Conflicts

If your PR has merge conflicts:

1. **Sync your branch with the target branch:**
   ```bash
   git fetch origin
   git merge origin/main  # or origin/develop for develop branch
   ```

2. **If conflicts occur, resolve them:**
   - Open conflicted files (marked with `<<<<<<<`, `=======`, `>>>>>>>`)
   - Manually resolve conflicts by choosing the correct code
   - Remove conflict markers
   - Test your changes to ensure functionality

3. **Stage and commit resolved files:**
   ```bash
   git add <resolved-files>
   git commit -m "chore: resolve merge conflicts with main"
   ```

4. **Verify no conflict markers remain:**
   ```bash
   # Pre-commit hook will check automatically
   git status
   ```

5. **Push updated branch:**
   ```bash
   git push origin your-branch-name
   ```

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

## Security Considerations

This repository implements security measures that affect the contribution workflow:

### Code Owner Review Requirements

- **Main Branch Protection**: All pull requests to `main` require status checks and pull request reviews
- **Critical Files**: Changes to protected files as defined in CODEOWNERS may receive additional review
- **CODEOWNERS**: The repository uses GitHub CODEOWNERS to define ownership but reviews are not automatically required

### Protected Configuration Files

The following files have defined code owners and may receive additional review:
- `.github/settings.yml` - Repository settings and automation
- `.github/CODEOWNERS` - Code ownership definitions  
- `SECURITY.md` - Security policies and procedures
- `.github/workflows/` - CI/CD pipeline configurations

### Development Impact

✅ **Note**: Code owner reviews are not automatically required, allowing for smoother workflow:
- **Pull requests** need to pass status checks and may receive review from code owners
- **Review response time** may affect development velocity
- **Plan ahead** for time-sensitive changes that need admin approval

For more details, see [SECURITY.md](../SECURITY.md).

## Submitting Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code quality guidelines

3. **If dependencies were modified, update the lock file:**
   ```bash
   # After editing pyproject.toml dependencies
   poetry lock --no-update  # Update only changed dependencies
   # or
   poetry lock  # Update all dependencies to latest compatible versions
   
   # Verify consistency
   poetry check
   ```

4. **Ensure all checks pass:**
   ```bash
   make check
   make test
   ```

5. **Resolve any merge conflicts with main branch:**
   ```bash
   # Fetch latest changes
   git fetch origin
   
   # Merge main into your branch
   git merge origin/main
   
   # If conflicts occur, resolve them manually, then:
   git add <resolved-files>
   git commit
   
   # Verify no conflict markers remain
   git diff origin/main
   ```

6. **Commit your changes** (pre-commit hooks will run automatically):
   ```bash
   git add .
   git commit -m "type(scope): description of your changes"
   ```
   
   **Note:** The pre-commit hook includes `check-merge-conflict` which will prevent commits with conflict markers.

7. **Push to your fork and create a pull request** with a properly formatted title:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Verify PR has no conflicts or failures:**
   - Check that PR shows "No conflicts with base branch"
   - Ensure all CI checks pass
   - Confirm `poetry.lock` is committed if dependencies changed

9. **Wait for code owner review** (required for all PRs to main branch)

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