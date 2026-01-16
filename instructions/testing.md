# Testing

## Test Structure, Containerized Testing, and Testing Patterns

### Testing Framework
- **Testing framework**: pytest with unit/integration separation
- **Markers**: `@pytest.mark.unit` for unit tests
- **Coverage**: pytest-cov for coverage reporting
- **Async testing**: pytest-asyncio for async tests

### Test Structure
```
tests/
├── unit/                          # Unit tests (mark with @pytest.mark.unit)
├── integration/                   # Integration tests
├── fixtures/                      # Test data and fixtures
└── test_*.py                      # Direct test files
```

### Testing Commands

#### Running Tests
```bash
# Run all tests
make test                        # 1-15 min, timeout 30+ min

# Run only unit tests (faster)
pytest tests/ -v -m "unit"       # 30 sec-2 min, timeout 10+ min

# Run integration tests
make test-integration            # 5-15 min, timeout 30+ min

# Run with coverage
make test-cov                    # 2-5 min, timeout 15+ min
```

#### Test Filtering
```bash
# Run specific test file
pytest tests/unit/test_scanner.py -v

# Run specific test function
pytest tests/unit/test_scanner.py::test_quick_scan -v

# Run tests matching pattern
pytest tests/ -k "scan" -v

# Run tests by marker
pytest tests/ -v -m "unit"
pytest tests/ -v -m "integration"
```

### Test Markers

#### Unit Tests
Mark unit tests with `@pytest.mark.unit`:
```python
import pytest

@pytest.mark.unit
def test_video_scanner_init():
    scanner = VideoScanner()
    assert scanner is not None
```

#### Integration Tests
Integration tests are in `tests/integration/`:
```python
@pytest.mark.integration
def test_ffmpeg_integration():
    result = run_ffmpeg_command(["--help"])
    assert result.returncode == 0
```

### Test Fixtures

#### Fixture Organization
- **Shared fixtures**: `tests/fixtures/` directory
- **Test data**: Sample video files, configuration files
- **conftest.py**: Common fixtures and configuration

#### Example Fixtures
```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_config():
    return {
        "logging": {"level": "INFO"},
        "ffmpeg": {"command": "/usr/bin/ffmpeg"}
    }

@pytest.fixture
def temp_video_dir(tmp_path):
    video_dir = tmp_path / "videos"
    video_dir.mkdir()
    return video_dir
```

### Testing Best Practices

#### Test Organization
- One test file per source module
- Group related tests in classes
- Use descriptive test names
- Keep tests focused and independent

#### Test Naming
```python
# Good test names
def test_scanner_finds_corrupted_videos()
def test_config_validates_required_fields()
def test_ffmpeg_timeout_handling()

# Clear and specific
```

#### Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- Don't rely on test execution order
- Clean up resources after tests

### Mocking and Patching

#### Using unittest.mock
```python
from unittest.mock import Mock, patch

@pytest.mark.unit
def test_ffmpeg_command_execution():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        
        result = execute_ffmpeg_command(["--help"])
        assert result.success
```

#### Mocking External Dependencies
- Mock FFmpeg calls in unit tests
- Mock file system operations
- Mock network requests
- Use real dependencies in integration tests

### Async Testing

#### pytest-asyncio
```python
import pytest

@pytest.mark.asyncio
async def test_async_video_processing():
    result = await process_video_async("video.mp4")
    assert result.status == "complete"
```

### Code Coverage

#### Coverage Configuration
```bash
# Run tests with coverage
make test-cov

# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/

# View coverage report
open htmlcov/index.html
```

#### Coverage Goals
- Aim for >80% coverage for critical modules
- Focus on business logic coverage
- Don't sacrifice test quality for coverage numbers

### Integration Testing

#### Video File Requirements
- Some integration tests require actual video files
- Use small sample files for testing
- Test both valid and corrupted videos
- Handle missing test files gracefully

#### FFmpeg Integration Tests
```python
@pytest.mark.integration
def test_ffmpeg_detects_corruption():
    result = scan_video("tests/fixtures/corrupted.mp4")
    assert result.is_corrupted
```

### Containerized Testing

#### Docker Test Environment
```bash
# Run tests in Docker container
make docker-test                 # Placeholder implementation

# Run specific tests in container
docker-compose run app pytest tests/unit/ -v
docker-compose run app pytest tests/integration/ -v
```

#### Benefits of Containerized Testing
- Consistent environment across all developers
- No dependency on host system configuration
- Isolated test execution
- Easy CI/CD integration

### Test Data Management

#### Test Fixtures Directory
```
tests/fixtures/
├── videos/
│   ├── valid.mp4
│   ├── corrupted.mp4
│   └── missing_frames.avi
├── configs/
│   ├── minimal.yaml
│   └── full.yaml
└── expected_outputs/
    └── scan_results.json
```

#### Generating Test Data
- Use FFmpeg to create test videos
- Generate various corruption scenarios
- Keep test files small (minimize repo size)
- Document test data creation process

### Parametrized Tests

#### Using pytest.mark.parametrize
```python
@pytest.mark.parametrize("mode,expected", [
    ("quick", 30),
    ("deep", 1800),
    ("hybrid", 60),
])
def test_scan_mode_timeout(mode, expected):
    timeout = get_scan_timeout(mode)
    assert timeout == expected
```

### Testing CLI

#### CLI Testing Strategies
```python
from typer.testing import CliRunner

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
```

#### Manual CLI Testing
```bash
# Create test configuration
cat > /tmp/config.yaml << 'EOF'
logging:
  level: INFO
ffmpeg:
  command: /usr/bin/ffmpeg
  quick_timeout: 30
EOF

# Test CLI commands
export PYTHONPATH=$(pwd)/src
python3 cli_handler.py --config /tmp/config.yaml --help
python3 cli_handler.py --config /tmp/config.yaml test-ffmpeg
```

### Performance Testing

#### Timing Tests
```python
import time

def test_scan_performance():
    start = time.time()
    scan_directory("/path/to/videos")
    duration = time.time() - start
    
    # Should complete within reasonable time
    assert duration < 60  # seconds
```

### Test Troubleshooting

#### Common Issues
- **Missing test videos**: Some integration tests require video files
- **Timeout errors**: Video processing can be slow
- **Import errors**: Set PYTHONPATH before running tests
- **Docker issues**: Ensure Docker service is running

#### Debugging Tests
```bash
# Run with verbose output
pytest tests/ -v -s

# Run with debug output
pytest tests/ --log-cli-level=DEBUG

# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/ --pdb
```

### Testing in Copilot Environment

#### Pre-installed Dependencies
- All test dependencies are pre-installed
- pytest, pytest-cov, pytest-asyncio available
- No network access required for testing
- Works with existing test suite

#### Quick Testing
```bash
# In Copilot environment
make test                        # All tests
pytest tests/ -v -m "unit"       # Unit tests only
```

### Continuous Integration Testing

#### CI/CD Pipeline
- Tests run automatically on push
- Separate jobs for unit and integration tests
- Coverage reports generated
- Test results published

#### Pre-commit Testing
```bash
# Setup pre-commit hooks
make pre-commit-install

# Runs on every commit:
# - Code formatting check
# - Linting
# - Type checking
# - Basic test suite (fast tests)
```

### Test Quality Guidelines

#### Writing Good Tests
- **Clear assertions**: One logical assertion per test
- **Descriptive names**: Test name explains what's tested
- **Minimal setup**: Use fixtures to reduce boilerplate
- **Fast execution**: Keep unit tests fast (<1 sec each)
- **Reliable**: No flaky tests, deterministic results

#### Test Documentation
- Add docstrings to complex tests
- Explain test data choices
- Document expected behaviors
- Link to related issues/PRs when relevant

### Test Maintenance

#### Keeping Tests Updated
- Update tests when requirements change
- Refactor tests with production code
- Remove obsolete tests
- Keep test fixtures current

#### Test Debt
- Address flaky tests immediately
- Don't skip tests without good reason
- Update deprecated testing patterns
- Maintain test coverage as code evolves

### Best Practices Summary
- **Mark unit tests** with `@pytest.mark.unit`
- **Keep tests independent** and isolated
- **Use fixtures** for setup and test data
- **Mock external dependencies** in unit tests
- **Test real integration** in integration tests
- **Maintain good coverage** (>80% for critical code)
- **Run tests before commits** (`make check && make test`)
- **Use Docker for consistency** when needed
- **Write clear, focused tests** with descriptive names
- **Keep tests fast** to encourage frequent running
