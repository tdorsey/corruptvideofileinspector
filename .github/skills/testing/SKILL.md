---
name: testing
description: Skill for test generation and analysis in the Corrupt Video File Inspector project
---

# Testing Skill

This skill provides comprehensive testing capabilities including test generation, analysis, and quality improvement for the Corrupt Video File Inspector project.

## Required Tools

### Allowed Tools

**Testing Framework (REQUIRED)**
- `pytest` - Test execution and framework
- `pytest-cov` - Coverage analysis
- `pytest-mock` - Mocking utilities
- `pytest-benchmark` - Performance testing

**Mocking and Fixtures (REQUIRED)**
- `unittest.mock` - Standard library mocking
- `fixtures` - Test data setup

**What to Use:**
```bash
# ✅ DO: Use pytest for all testing
pytest tests/ -v
pytest tests/unit/ -m unit
pytest tests/ --cov=src --cov-report=html

# ✅ DO: Use pytest markers
pytest -m "unit and not slow"
pytest -m integration

# ✅ DO: Use coverage tools
coverage run -m pytest tests/
coverage report --show-missing
```

**What NOT to Use:**
```bash
# ❌ DON'T: Use other test frameworks
unittest                    # Use pytest instead
nose                        # Deprecated, use pytest
nose2                       # Use pytest instead

# ❌ DON'T: Use non-standard test runners
python -m unittest discover # Use pytest instead

# ❌ DON'T: Create custom test frameworks
# Use pytest's built-in features instead
```

### Tool Usage Examples

**Example 1: Run Tests with Coverage**
```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Run only unit tests
pytest tests/unit/ -v -m unit

# Run specific test file
pytest tests/unit/test_scanner.py -v
```

**Example 2: Use Mocking**
```python
from unittest.mock import Mock, patch
import pytest

@pytest.mark.unit
def test_with_mock(mocker):
    """Use pytest-mock for mocking."""
    mock_ffmpeg = mocker.patch("src.ffmpeg.run_command")
    mock_ffmpeg.return_value = Mock(returncode=0, stdout="OK")
    
    result = scan_video("/test.mp4")
    
    assert result.status == "healthy"
    mock_ffmpeg.assert_called_once()
```

**Example 3: Performance Testing**
```python
@pytest.mark.benchmark
def test_scan_performance(benchmark):
    """Benchmark video scanning."""
    result = benchmark(scan_video, sample_video_path)
    assert result.status in ["healthy", "corrupt"]
```

**Example 4: Check Coverage**
```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Fail if coverage below threshold
pytest tests/ --cov=src --cov-fail-under=80
```

## When to Use

Use this skill when:
- Writing tests for new functionality
- Analyzing test coverage and gaps
- Improving test quality and maintainability
- Debugging failing tests
- Setting up test fixtures and mocks
- Running and interpreting test results

## Test Organization

### Directory Structure

```
tests/
├── unit/                       # Unit tests (fast, isolated)
│   ├── test_scanner.py
│   ├── test_config.py
│   └── test_ffmpeg.py
├── integration/                # Integration tests
│   ├── test_cli_workflow.py
│   └── test_docker_scan.py
├── fixtures/                   # Test data and fixtures
│   ├── sample_videos/
│   └── conftest.py             # Shared fixtures
└── conftest.py                 # Root fixtures and configuration
```

### Test Markers

**Required Markers**
```python
@pytest.mark.unit              # Fast, isolated unit tests
@pytest.mark.integration       # Component integration tests
```

**Optional Markers**
```python
@pytest.mark.slow              # Tests taking >5 seconds
@pytest.mark.docker            # Tests requiring Docker
@pytest.mark.network           # Tests requiring network access
```

## Test Writing Standards

### Test Structure (Arrange-Act-Assert)

```python
@pytest.mark.unit
def test_scan_video_returns_healthy_for_valid_file() -> None:
    """Test that scanning a valid video returns healthy status."""
    # Arrange: Set up test data and expectations
    video_path = Path("/tmp/test_video.mp4")
    scanner = VideoScanner(config)
    expected_status = "healthy"
    
    # Act: Execute the function being tested
    result = scanner.scan(video_path)
    
    # Assert: Verify the results
    assert result.status == expected_status
    assert result.path == video_path
```

### Naming Conventions

**Test Files**
- Prefix with `test_`: `test_scanner.py`
- Match source file name: `scanner.py` → `test_scanner.py`
- Place in appropriate directory (unit/ or integration/)

**Test Functions**
```python
def test_<function>_<scenario>_<expected_outcome>() -> None:
    """Docstring describing what is being tested."""
    ...

# Examples:
def test_scan_video_with_valid_file_returns_healthy() -> None:
def test_validate_config_with_missing_field_raises_error() -> None:
def test_parse_output_with_empty_string_returns_none() -> None:
```

### Type Annotations

All test functions must have type annotations:
```python
from pathlib import Path
from typing import List, Optional
import pytest

@pytest.mark.unit
def test_function(
    sample_data: List[str],
    tmp_path: Path
) -> None:
    """Test description."""
    ...
```

## Pytest Fixtures

### Built-in Fixtures

```python
# tmp_path - Temporary directory (Path object)
def test_with_temp_dir(tmp_path: Path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()

# monkeypatch - Mock/patch objects
def test_with_mock(monkeypatch) -> None:
    monkeypatch.setattr("os.environ", {"KEY": "value"})
    ...

# capsys - Capture stdout/stderr
def test_output(capsys) -> None:
    print("test output")
    captured = capsys.readouterr()
    assert captured.out == "test output\n"
```

### Custom Fixtures

**Define in conftest.py**
```python
import pytest
from pathlib import Path
from src.config import Config

@pytest.fixture
def sample_config() -> Config:
    """Provide a test configuration."""
    return Config(
        logging=LogConfig(level="INFO"),
        ffmpeg=FFmpegConfig(command="/usr/bin/ffmpeg"),
        # ... other config
    )

@pytest.fixture
def sample_video(tmp_path: Path) -> Path:
    """Provide a sample video file for testing."""
    video_path = tmp_path / "sample.mp4"
    # Create or copy sample video
    return video_path
```

**Use fixtures in tests**
```python
@pytest.mark.unit
def test_scan_with_config(
    sample_config: Config,
    sample_video: Path
) -> None:
    """Test scanning with custom config."""
    scanner = VideoScanner(sample_config)
    result = scanner.scan(sample_video)
    assert result is not None
```

### Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default, run for each test
def per_test_fixture():
    ...

@pytest.fixture(scope="module")    # Run once per module
def per_module_fixture():
    ...

@pytest.fixture(scope="session")   # Run once per session
def per_session_fixture():
    ...
```

## Mocking and Patching

### Mock External Dependencies

**Using unittest.mock**
```python
from unittest.mock import Mock, MagicMock, patch
import pytest

@pytest.mark.unit
def test_ffmpeg_call() -> None:
    """Test FFmpeg execution without calling real FFmpeg."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="success",
            stderr=""
        )
        
        result = run_ffmpeg_scan("/path/to/video")
        
        assert result.success
        mock_run.assert_called_once()
```

**Using pytest-mock**
```python
@pytest.mark.unit
def test_with_mocker(mocker) -> None:
    """Test using pytest-mock plugin."""
    mock_ffmpeg = mocker.patch("src.ffmpeg.scanner.FFmpegScanner")
    mock_ffmpeg.scan.return_value = ScanResult(status="healthy")
    
    result = scan_video("/path/to/video")
    
    assert result.status == "healthy"
```

### Mock File System

```python
@pytest.mark.unit
def test_file_operations(tmp_path: Path) -> None:
    """Test file operations using temporary directory."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    result = process_file(test_file)
    
    assert result == "processed: test content"
```

### Mock Environment Variables

```python
@pytest.mark.unit
def test_env_config(monkeypatch) -> None:
    """Test configuration with environment variables."""
    monkeypatch.setenv("FFMPEG_TIMEOUT", "60")
    
    config = load_config()
    
    assert config.ffmpeg_timeout == 60
```

## Parametrized Tests

### Basic Parametrization

```python
@pytest.mark.unit
@pytest.mark.parametrize("input_val,expected", [
    ("valid.mp4", True),
    ("invalid.txt", False),
    ("video.mkv", True),
    ("", False),
])
def test_video_file_validation(
    input_val: str, expected: bool
) -> None:
    """Test video file validation with various inputs."""
    result = is_valid_video_file(input_val)
    assert result == expected
```

### Multiple Parameters

```python
@pytest.mark.unit
@pytest.mark.parametrize("mode,timeout,expected_calls", [
    ("quick", 30, 1),
    ("deep", 1800, 2),
    ("hybrid", 60, 2),
])
def test_scan_modes(
    mode: str,
    timeout: int,
    expected_calls: int,
    mocker
) -> None:
    """Test different scan modes."""
    mock_ffmpeg = mocker.patch("src.ffmpeg.run_scan")
    
    scan_video("/path/to/video", mode=mode)
    
    assert mock_ffmpeg.call_count == expected_calls
```

### Parametrize with IDs

```python
@pytest.mark.unit
@pytest.mark.parametrize(
    "config,expected",
    [
        ({"timeout": 30}, 30),
        ({"timeout": 60}, 60),
        ({}, 30),  # default
    ],
    ids=["explicit-30", "explicit-60", "default"]
)
def test_timeout_config(config: dict, expected: int) -> None:
    """Test timeout configuration."""
    result = Config(**config).timeout
    assert result == expected
```

## Test Coverage

### Running Tests with Coverage

```bash
# Run all tests with coverage
make test-cov

# Run specific tests with coverage
pytest tests/unit/test_scanner.py --cov=src.scanner --cov-report=html

# Run with coverage threshold
pytest --cov=src --cov-fail-under=80
```

### Coverage Requirements

- **Minimum overall coverage**: 80%
- **New code coverage**: 90%
- **Critical modules coverage**: 95%

### Coverage Gaps to Address

1. **Untested functions**: Add unit tests
2. **Untested branches**: Add parametrized tests for conditions
3. **Untested error paths**: Add exception tests
4. **Untested edge cases**: Add boundary tests

## Testing Patterns

### Testing Exceptions

```python
@pytest.mark.unit
def test_invalid_path_raises_error() -> None:
    """Test that invalid path raises ValueError."""
    with pytest.raises(ValueError, match="Invalid path"):
        process_video("/nonexistent/path")
```

### Testing Async Code

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_function() -> None:
    """Test asynchronous function."""
    result = await async_scan_video("/path/to/video")
    assert result.status == "complete"
```

### Testing CLI Commands

```python
from typer.testing import CliRunner
from src.cli.main import app

runner = CliRunner()

@pytest.mark.unit
def test_cli_scan_command() -> None:
    """Test CLI scan command."""
    result = runner.invoke(app, ["scan", "--directory", "/tmp"])
    
    assert result.exit_code == 0
    assert "Scan complete" in result.stdout
```

### Testing Configuration

```python
@pytest.mark.unit
def test_config_loading(tmp_path: Path) -> None:
    """Test configuration loading from file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
    logging:
      level: DEBUG
    ffmpeg:
      command: /usr/bin/ffmpeg
    """)
    
    config = Config.load(config_file)
    
    assert config.logging.level == "DEBUG"
    assert config.ffmpeg.command == Path("/usr/bin/ffmpeg")
```

## Integration Testing

### Docker Integration Tests

```python
@pytest.mark.integration
@pytest.mark.docker
def test_docker_scan_workflow() -> None:
    """Test complete scan workflow in Docker."""
    # Setup: Create test videos in mounted volume
    # Execute: Run docker-compose scan command
    # Assert: Verify output files and results
    ...
```

### FFmpeg Integration Tests

```python
@pytest.mark.integration
def test_ffmpeg_scan_real_video(sample_video: Path) -> None:
    """Test FFmpeg scanning with actual video file."""
    scanner = FFmpegScanner(config)
    
    result = scanner.scan(sample_video)
    
    assert result.status in ["healthy", "corrupt", "error"]
    assert result.path == sample_video
```

## Test Quality Guidelines

### Test Independence

- Each test should be runnable in isolation
- Tests should not depend on execution order
- Clean up test data after each test
- Don't share mutable state between tests

### Test Clarity

```python
# Good: Clear, descriptive test
@pytest.mark.unit
def test_scan_video_with_corrupt_file_returns_corrupt_status() -> None:
    """Test that scanning a corrupt video returns corrupt status."""
    corrupt_video = create_corrupt_video()
    scanner = VideoScanner()
    
    result = scanner.scan(corrupt_video)
    
    assert result.status == "corrupt"

# Bad: Unclear, generic test
@pytest.mark.unit
def test_scan() -> None:
    result = scan_video("test.mp4")
    assert result
```

### Test Speed

- Unit tests: <5 seconds per test
- Integration tests: <30 seconds per test
- Use mocks to avoid slow operations
- Use `pytest.mark.slow` for unavoidably slow tests

### Test Assertions

```python
# Good: Specific assertions
assert result.status == "healthy"
assert result.errors == []
assert len(result.warnings) == 2

# Bad: Vague assertions
assert result
assert result.status
```

## Debugging Tests

### Running Specific Tests

```bash
# Run single test
pytest tests/unit/test_scanner.py::test_scan_video_success

# Run tests matching pattern
pytest -k "test_scan"

# Run tests with specific marker
pytest -m unit

# Run with verbose output
pytest -v

# Show print statements
pytest -s
```

### Debug with pdb

```python
@pytest.mark.unit
def test_complex_logic() -> None:
    """Test with debugging."""
    import pdb; pdb.set_trace()  # Set breakpoint
    
    result = complex_function()
    assert result == expected
```

### Test Failures

```bash
# Show local variables on failure
pytest --showlocals

# Stop on first failure
pytest -x

# Show full diff
pytest -vv
```

## Common Testing Mistakes

### Avoid These Patterns

**Testing Implementation Instead of Behavior**
```python
# Bad: Testing internal implementation
def test_scan_calls_ffmpeg_with_correct_args():
    # Tests how it works, not what it does
    ...

# Good: Testing behavior/outcome
def test_scan_returns_correct_status_for_valid_video():
    # Tests what it produces
    ...
```

**Brittle Tests**
```python
# Bad: Depends on exact string format
assert str(result) == "Status: healthy, Duration: 120.5"

# Good: Tests specific values
assert result.status == "healthy"
assert result.duration == 120.5
```

**Shared Mutable State**
```python
# Bad: Global state affects tests
shared_list = []

def test_a():
    shared_list.append(1)  # Affects other tests

# Good: Use fixtures
@pytest.fixture
def clean_list():
    return []
```

## Example Test Suite

### Complete Test File Example

```python
"""Tests for video scanner module."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from src.scanner import VideoScanner, ScanResult
from src.config import Config

@pytest.fixture
def scanner_config() -> Config:
    """Provide test configuration."""
    return Config(
        ffmpeg={"command": "/usr/bin/ffmpeg", "timeout": 30},
        logging={"level": "INFO"}
    )

@pytest.fixture
def video_scanner(scanner_config: Config) -> VideoScanner:
    """Provide configured scanner instance."""
    return VideoScanner(scanner_config)

@pytest.mark.unit
def test_scan_video_with_valid_file(
    video_scanner: VideoScanner,
    tmp_path: Path
) -> None:
    """Test scanning a valid video file."""
    # Arrange
    video_file = tmp_path / "test.mp4"
    video_file.touch()
    
    # Act
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=0, stdout="OK")
        result = video_scanner.scan(video_file)
    
    # Assert
    assert result.status == "healthy"
    assert result.path == video_file

@pytest.mark.unit
@pytest.mark.parametrize("return_code,expected_status", [
    (0, "healthy"),
    (1, "corrupt"),
    (-1, "error"),
])
def test_scan_video_with_different_return_codes(
    video_scanner: VideoScanner,
    return_code: int,
    expected_status: str,
    tmp_path: Path
) -> None:
    """Test scanner handles different FFmpeg return codes."""
    video_file = tmp_path / "test.mp4"
    video_file.touch()
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = Mock(returncode=return_code)
        result = video_scanner.scan(video_file)
    
    assert result.status == expected_status

@pytest.mark.unit
def test_scan_nonexistent_file_raises_error(
    video_scanner: VideoScanner
) -> None:
    """Test that scanning nonexistent file raises error."""
    with pytest.raises(FileNotFoundError):
        video_scanner.scan(Path("/nonexistent/video.mp4"))
```

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
