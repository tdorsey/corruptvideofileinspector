---
name: code-review
description: Skill for performing code reviews in the Corrupt Video File Inspector project
---

# Code Review Skill

This skill provides capabilities for automated code review, ensuring code quality, standards compliance, and best practices in the Corrupt Video File Inspector project.

## Required Tools

### Allowed Tools

**Code Quality Tools (REQUIRED)**
- `black` - Code formatting verification
- `ruff` - Python linting
- `mypy` - Type checking
- `pytest` - Running and validating tests
- `grep` / `view` - Code inspection
- `git diff` - Reviewing changes

**Security Tools (RECOMMENDED)**
- `bandit` - Python security linting (when available)
- GitHub security scanning APIs

**What to Use:**
```bash
# ✅ DO: Use project-standard tools
make check           # Runs black, ruff, mypy
make test            # Runs pytest
git diff HEAD~1      # Review recent changes

# ✅ DO: Use grep for pattern searching
grep -r "hardcoded_password" src/

# ✅ DO: Use view to inspect specific files
# (via view tool in agent context)
```

**What NOT to Use:**
```bash
# ❌ DON'T: Use non-standard linters
pylint               # Use ruff instead
flake8               # Use ruff instead
autopep8             # Use black instead

# ❌ DON'T: Run arbitrary security scanners
# without project approval
pip install some-random-scanner

# ❌ DON'T: Modify code during review
# Reviews should only analyze, not change code
```

### Tool Usage Examples

**Example 1: Check Code Quality**
```bash
# Verify formatting
black src/ tests/ --check

# Run linter
ruff check src/ tests/

# Type check
mypy src/ tests/
```

**Example 2: Review for Security Issues**
```bash
# Search for potential secrets
grep -rn "password\s*=\s*['\"]" src/
grep -rn "api_key\s*=\s*['\"]" src/

# Check for SQL injection risks
grep -rn "execute.*%.*%" src/
```

**Example 3: Validate Test Coverage**
```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Check if new code has tests
git diff HEAD~1 --name-only | grep "^src/" | while read f; do
  test_file="tests/unit/test_${f#src/}"
  [ -f "$test_file" ] || echo "Missing tests for $f"
done
```

## When to Use

Use this skill when:
- Reviewing pull requests for code quality
- Validating adherence to project coding standards
- Checking for common Python anti-patterns
- Ensuring test coverage and documentation
- Identifying security vulnerabilities

## Code Quality Standards

### Python Standards

**Type Annotations (REQUIRED)**
- All function parameters must have type annotations
- All function return types must be specified
- Use `typing` module for complex types
- Example:
  ```python
  def scan_video(path: Path, mode: str = "quick") -> ScanResult:
      ...
  ```

**Formatting (REQUIRED)**
- Line length: Maximum 79 characters
- Use Black for formatting
- Use f-strings for string formatting (NOT .format() or %)
- Example:
  ```python
  # Good
  message = f"Scanning {count} files in {directory}"
  
  # Bad
  message = "Scanning {} files in {}".format(count, directory)
  message = "Scanning %s files in %s" % (count, directory)
  ```

**Import Organization (REQUIRED)**
- Group imports: standard library, third-party, local
- Sort alphabetically within groups
- One import per line
- Example:
  ```python
  # Standard library
  import os
  from pathlib import Path
  from typing import List, Optional
  
  # Third-party
  import click
  import pydantic
  
  # Local
  from src.config import Config
  from src.scanner import VideoScanner
  ```

### Testing Standards

**Unit Tests (REQUIRED)**
- All new functions must have unit tests
- Use pytest markers: `@pytest.mark.unit`
- Test file naming: `test_<module>.py`
- Test function naming: `test_<function>_<scenario>`
- Example:
  ```python
  @pytest.mark.unit
  def test_scan_video_with_valid_file(tmp_path: Path) -> None:
      """Test scanning a valid video file."""
      ...
  ```

**Test Coverage**
- Aim for >80% code coverage
- Test edge cases and error conditions
- Include parametrized tests for multiple scenarios
- Mock external dependencies (FFmpeg, API calls)

### Documentation Standards

**Docstrings (REQUIRED for public APIs)**
- Use Google-style docstrings
- Include description, parameters, returns, and raises
- Example:
  ```python
  def scan_directory(
      directory: Path,
      recursive: bool = True
  ) -> List[ScanResult]:
      """Scan a directory for corrupt video files.
      
      Args:
          directory: Path to the directory to scan
          recursive: Whether to scan subdirectories
          
      Returns:
          List of scan results for each video file
          
      Raises:
          ValueError: If directory does not exist
          PermissionError: If directory is not readable
      """
      ...
  ```

**Comments**
- Use comments sparingly
- Explain "why", not "what"
- Comment complex algorithms or non-obvious logic
- Avoid redundant comments

## Review Checklist

### Critical Items (Must Fix)
- [ ] All functions have type annotations
- [ ] No lines exceed 79 characters
- [ ] f-strings used for formatting
- [ ] All tests pass (`make test`)
- [ ] Code formatting passes (`make check`)
- [ ] No hardcoded secrets or credentials
- [ ] Imports are properly organized
- [ ] New code has unit tests

### Important Items (Should Fix)
- [ ] Public functions have docstrings
- [ ] Error handling is appropriate
- [ ] Edge cases are tested
- [ ] Documentation is updated
- [ ] Conventional commit messages used
- [ ] No commented-out code
- [ ] Variable names are descriptive

### Nice-to-Have Items (Optional)
- [ ] Code is DRY (Don't Repeat Yourself)
- [ ] Functions are small and focused
- [ ] Complex logic has explanatory comments
- [ ] Performance is optimized where needed

## Common Code Smells

### Anti-Patterns to Detect

**Hardcoded Values**
```python
# Bad
timeout = 30
api_url = "https://api.example.com"

# Good
timeout = config.ffmpeg.quick_timeout
api_url = config.api.base_url
```

**Missing Error Handling**
```python
# Bad
def read_file(path: str) -> str:
    return open(path).read()

# Good
def read_file(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
```

**Overly Complex Functions**
```python
# Bad: 100+ line function with multiple responsibilities

# Good: Break into smaller, focused functions
def process_video(path: Path) -> ScanResult:
    """Process a single video file."""
    if not validate_video(path):
        return ScanResult(status="invalid")
    
    metadata = extract_metadata(path)
    health = check_health(path, metadata)
    
    return create_result(path, metadata, health)
```

**Mutable Default Arguments**
```python
# Bad
def scan_videos(paths: list = []) -> None:
    ...

# Good
def scan_videos(paths: Optional[List[Path]] = None) -> None:
    if paths is None:
        paths = []
    ...
```

## Security Considerations

### Critical Security Checks

**Secrets Detection**
- No API keys, passwords, or tokens in code
- Use environment variables or Docker secrets
- Check for accidental commits of `.env` files

**Input Validation**
- Validate all user inputs
- Sanitize file paths
- Check file types before processing
- Limit file sizes

**Command Injection**
- Use subprocess with list arguments, not shell=True
- Validate command parameters
- Escape special characters in file paths

**Error Information Disclosure**
- Don't expose internal paths in error messages
- Sanitize stack traces in production
- Log sensitive errors without displaying to users

## Project-Specific Patterns

### Configuration Access
```python
# Use Pydantic models from config module
from src.config import Config

config = Config.load()
timeout = config.ffmpeg.quick_timeout
```

### CLI Commands
```python
# Use Typer for CLI commands
import typer

app = typer.Typer()

@app.command()
def scan(
    directory: Path,
    mode: str = typer.Option("quick", help="Scan mode")
) -> None:
    """Scan directory for corrupt videos."""
    ...
```

### FFmpeg Integration
```python
# Use the ffmpeg module wrapper
from src.ffmpeg import FFmpegScanner

scanner = FFmpegScanner(config)
result = scanner.scan_video(video_path)
```

### Docker Integration
- Respect volume mounts defined in docker-compose.yml
- Use Docker secrets for sensitive data
- Test changes in containerized environment

## Review Process

### Step-by-Step Review

1. **Initial Scan**
   - Check file changes in PR
   - Identify scope and impact
   - Review commit messages

2. **Code Analysis**
   - Run automated checks (`make check`)
   - Review type annotations
   - Check formatting and style
   - Verify imports

3. **Logic Review**
   - Understand code purpose
   - Check algorithm correctness
   - Verify error handling
   - Assess code complexity

4. **Testing Review**
   - Verify test existence
   - Check test quality
   - Run tests (`make test`)
   - Review test coverage

5. **Security Review**
   - Check for hardcoded secrets
   - Verify input validation
   - Review command execution
   - Assess error handling

6. **Documentation Review**
   - Check docstrings
   - Verify README updates
   - Review inline comments
   - Validate examples

### Providing Feedback

**Format**
```markdown
### Summary
Brief overview of changes and overall assessment.

### Critical Issues
1. **File: src/scanner.py, Line 42**
   - Issue: Missing type annotation on `process_files` function
   - Fix: Add return type annotation
   
2. **File: src/cli.py, Line 15**
   - Issue: Line exceeds 79 characters
   - Fix: Break line or simplify expression

### Suggestions
1. Consider extracting repeated logic into a helper function
2. Add edge case test for empty directory

### Positive Notes
- Excellent test coverage
- Clear, descriptive variable names
- Good error handling
```

## Example Review Scenarios

### Scenario 1: New Feature Addition

**Files Changed**: `src/scanner.py`, `tests/test_scanner.py`

**Review Points**:
- Does the feature match the issue requirements?
- Are type annotations present?
- Are unit tests comprehensive?
- Is documentation updated?
- Does it follow existing patterns?

### Scenario 2: Bug Fix

**Files Changed**: `src/ffmpeg/scanner.py`

**Review Points**:
- Does the fix address the root cause?
- Are edge cases handled?
- Is there a test to prevent regression?
- Is the fix minimal and focused?

### Scenario 3: Refactoring

**Files Changed**: Multiple files

**Review Points**:
- Does behavior remain unchanged?
- Are tests still passing?
- Is the code more maintainable?
- Is performance maintained or improved?

## Tools and Commands

### Pre-Review Commands
```bash
# Format code
make format

# Run linters
make lint

# Type check
make type

# Run all checks
make check

# Run tests
make test

# Run with coverage
make test-cov
```

### Review Validation
```bash
# Check specific file
black src/scanner.py --check
ruff check src/scanner.py
mypy src/scanner.py

# Run specific tests
pytest tests/test_scanner.py -v
```

## References

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Ruff Linter](https://docs.astral.sh/ruff/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Project Contributing Guide](../../CONTRIBUTING.md)
