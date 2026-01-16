---
applyTo: "tests/**/*.py"
---

# Pytest Test Requirements

When writing pytest tests for this repository, follow these guidelines to ensure consistency, maintainability, and alignment with project standards.

## Test Structure

### Required Test Markers
- Mark unit tests with `@pytest.mark.unit`
- Mark integration tests with `@pytest.mark.integration`
- Unit tests should be fast (<100ms) and not require external dependencies
- Integration tests can be slower and test with actual FFmpeg/files

### Test File Naming
- Unit tests: `tests/unit/test_<module>.py`
- Integration tests: `tests/integration/test_<workflow>.py`
- Test functions: `test_<behavior>_<condition>_<expected_result>()`

## Testing Conventions

### 1. Use Descriptive Test Names
```python
# Good
def test_scanner_detects_corrupted_video_with_missing_codec():
    pass

# Bad
def test_scanner():
    pass
```

### 2. Follow Arrange-Act-Assert Pattern
```python
def test_formatter_generates_valid_json():
    # Arrange
    results = [ScanResult(...)]
    formatter = JSONFormatter()
    
    # Act
    output = formatter.format(results)
    
    # Assert
    assert json.loads(output)  # Valid JSON
    assert output['total'] == 1
```

### 3. Use Fixtures for Common Setup
- Place fixtures in `tests/conftest.py` or test file
- Use `pytest.fixture` decorator
- Prefer function-scoped fixtures unless state reuse is beneficial

### 4. Mock External Dependencies
- Mock FFmpeg subprocess calls in unit tests
- Use `unittest.mock` or `pytest-mock`
- Don't mock the code under test

### 5. Test Edge Cases
- Empty inputs
- None/null values
- Invalid data types
- Boundary conditions
- Error conditions

## Code Quality in Tests

### Type Annotations
- Always use type hints in test functions
- Annotate fixtures with return types
- Use `typing` module for complex types

### Assertions
- Use specific assertions: `assert x == y`, not `assert x`
- Use `pytest.raises()` for exception testing
- Add assertion messages for clarity when needed

### Test Independence
- Each test must run independently
- Don't rely on test execution order
- Clean up resources in teardown or use fixtures

## Coverage Requirements

- Aim for >95% coverage for core modules
- 100% coverage for critical paths (scanner, FFmpeg wrapper)
- Use `pytest --cov=src --cov-report=term-missing` to check
- Don't test private methods directly unless necessary

## Example Test Structure

```python
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.core.scanner import VideoScanner
from src.core.models import ScanResult, Status


@pytest.mark.unit
def test_scanner_processes_valid_video():
    """Test that scanner correctly processes a healthy video file."""
    # Arrange
    video_path = Path("/path/to/video.mp4")
    scanner = VideoScanner(mode="quick", timeout=30)
    
    with patch('src.ffmpeg.wrapper.FFmpegWrapper.probe') as mock_probe:
        mock_probe.return_value = {
            'duration': 120.5,
            'codec': 'h264',
            'errors': []
        }
        
        # Act
        result = scanner.scan_file(video_path)
        
        # Assert
        assert result.status == Status.HEALTHY
        assert result.duration == 120.5
        assert result.codec == 'h264'
        assert len(result.errors) == 0
        mock_probe.assert_called_once_with(video_path)


@pytest.mark.integration
def test_scanner_detects_actual_corrupted_video(tmp_path):
    """Integration test with real video file."""
    # Arrange
    video_file = tmp_path / "corrupt.mp4"
    # Create actual corrupted video file
    video_file.write_bytes(b'invalid video data')
    
    scanner = VideoScanner(mode="deep", timeout=60)
    
    # Act
    result = scanner.scan_file(video_file)
    
    # Assert
    assert result.status == Status.CORRUPTED
    assert len(result.errors) > 0
```

## Common Testing Patterns

### Testing CLI Commands
```python
from typer.testing import CliRunner
from src.cli.app import app

def test_scan_command_with_json_output():
    runner = CliRunner()
    result = runner.invoke(app, ["scan", "/path", "--output-json"])
    assert result.exit_code == 0
    assert "results" in result.stdout
```

### Testing with Temporary Files
```python
def test_output_formatter_writes_to_file(tmp_path):
    output_file = tmp_path / "results.json"
    formatter = JSONFormatter()
    formatter.write(results, output_file)
    assert output_file.exists()
    assert output_file.read_text()
```

### Parametrized Tests
```python
@pytest.mark.parametrize("mode,expected_timeout", [
    ("quick", 30),
    ("deep", 1800),
    ("hybrid", 300),
])
def test_scanner_uses_correct_timeout(mode, expected_timeout):
    scanner = VideoScanner(mode=mode)
    assert scanner.timeout == expected_timeout
```

## Running Tests

```bash
# All tests
make test

# Unit tests only (fast)
pytest tests/ -v -m "unit"

# Integration tests only
pytest tests/ -v -m "integration"

# With coverage
make test-cov

# Specific test file
pytest tests/unit/test_scanner.py -v

# Specific test
pytest tests/unit/test_scanner.py::test_scanner_processes_valid_video -v
```

## Pre-Commit Requirements

- Run `make check` before committing (black, ruff, mypy)
- Ensure all tests pass: `make test`
- Check coverage for new code
- Fix any linting or type checking errors

## Don't Do

- ❌ Don't skip markers (`@pytest.mark.unit` or `@pytest.mark.integration`)
- ❌ Don't test implementation details
- ❌ Don't use sleep() - use proper mocking/waiting
- ❌ Don't leave commented-out code
- ❌ Don't ignore type checking errors in tests
- ❌ Don't use hard-coded paths - use `tmp_path` fixture
- ❌ Don't test multiple things in one test

## Summary

Good tests are:
- **Fast** (unit tests <100ms)
- **Isolated** (no dependencies on other tests)
- **Repeatable** (same result every time)
- **Self-checking** (clear pass/fail)
- **Timely** (written with or before code)
