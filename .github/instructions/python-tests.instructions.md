---
applyTo: "tests/**/*.py"
---

# Python Test File Instructions

When writing or modifying test files in this repository, follow these guidelines:

## Test Framework and Structure

- **Framework**: pytest with markers for unit and integration tests
- **Markers Required**: All tests must use `@pytest.mark.unit` or `@pytest.mark.integration`
- **File Naming**: Test files must start with `test_` (e.g., `test_scanner.py`)
- **Function Naming**: Test functions must start with `test_` and be descriptive

## Test Organization

```python
# tests/unit/test_scanner.py
import pytest
from src.core.scanner import VideoScanner

@pytest.mark.unit
def test_scanner_init_with_valid_directory(tmp_path):
    """Test VideoScanner initializes with valid directory."""
    scanner = VideoScanner(str(tmp_path))
    assert scanner.directory == str(tmp_path)
```

## Required Guidelines

1. **Use pytest markers** - Every test MUST have either `@pytest.mark.unit` or `@pytest.mark.integration`
2. **Type annotations** - Include type hints for test functions and fixtures
3. **Descriptive names** - Test names should clearly describe what they test: `test_function_scenario_expected`
4. **Use fixtures** - Leverage pytest fixtures for common setup (tmp_path, monkeypatch, etc.)
5. **Isolation** - Each test should be independent and not rely on other tests' state
6. **Arrange-Act-Assert** - Follow AAA pattern for test structure
7. **Coverage target** - Aim for 80%+ coverage for new code

## Test Types

### Unit Tests (`@pytest.mark.unit`)
- Fast, isolated tests
- Mock external dependencies (FFmpeg, file I/O, API calls)
- Test individual functions/classes
- Located in `tests/unit/`

### Integration Tests (`@pytest.mark.integration`)
- Test multiple components working together
- May use real FFmpeg calls or file operations
- Slower execution acceptable
- Located in `tests/integration/`

## Mocking External Dependencies

Always mock FFmpeg subprocess calls in unit tests:

```python
@pytest.mark.unit
def test_ffmpeg_runner_handles_error(monkeypatch):
    """Test FFmpeg runner handles subprocess errors."""
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, 'ffmpeg')
    
    monkeypatch.setattr('subprocess.run', mock_run)
    # Test implementation
```

## Parametrized Tests

Use `@pytest.mark.parametrize` for testing multiple scenarios:

```python
@pytest.mark.unit
@pytest.mark.parametrize("extension,expected", [
    (".mp4", True),
    (".mkv", True),
    (".txt", False),
])
def test_is_video_file(extension, expected):
    """Test video file extension detection."""
    assert is_video_file(f"test{extension}") == expected
```

## Common Fixtures

- `tmp_path` - Temporary directory for file operations
- `monkeypatch` - Monkey-patching for mocking
- `caplog` - Capture log messages
- Custom fixtures in `tests/fixtures/conftest.py`

## Running Tests

```bash
# All tests
make test

# Unit tests only (fast)
pytest tests/ -v -m "unit"

# Integration tests
pytest tests/ -v -m "integration"

# With coverage
pytest --cov=src tests/
```

## Common Mistakes to Avoid

❌ Missing pytest markers
❌ Tests depending on execution order
❌ Hardcoded file paths
❌ Not mocking external dependencies in unit tests
❌ Overly complex test setup
❌ Testing implementation details instead of behavior
