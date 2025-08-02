# Testing Documentation

The Corrupt Video Inspector includes a comprehensive testing suite covering unit tests, integration tests, and end-to-end workflows. This document describes the testing framework, how to run tests, and the testing philosophy.

## Test Structure

```
tests/
├── fixtures/               # Test data and video samples
│   └── test-videos/       # Sample video files for testing
├── test_cli_*.py          # CLI module tests
├── test_core_*.py         # Core module tests  
├── test_config.py         # Configuration tests
├── test_utils*.py         # Utility function tests
├── test_video_inspector*.py # Video inspection tests
├── test_trakt_*.py        # Trakt integration tests
├── test_signal_*.py       # Signal handling tests
└── test_end_to_end_*.py   # Complete workflow tests
```

## Test Categories

### Unit Tests
Fast, isolated tests that verify individual functions and components:

- **CLI Tests** (`test_cli_*.py`) - Command parsing, handlers, and CLI utilities
- **Core Tests** (`test_core_*.py`) - Scanner, inspector, reporter, and watchlist components
- **Utils Tests** (`test_utils*.py`) - Utility functions and helpers
- **Config Tests** (`test_config.py`) - Configuration system and validation
- **Video Inspector** (`test_video_inspector*.py`) - Video analysis and corruption detection

### Integration Tests
End-to-end tests validating complete workflows and component interactions:

- **CLI Integration** (`test_cli_integration.py`) - Complete CLI command execution
- **Video Inspector Integration** (`test_video_inspector_integration.py`) - FFmpeg integration
- **Utils Integration** (`test_utils_integration.py`) - Cross-component utility usage
- **End-to-End** (`test_end_to_end_*.py`) - Complete application workflows

### Specialized Tests
- **Signal Handling** (`test_signal_*.py`) - Graceful shutdown and resume functionality
- **Trakt Integration** (`test_trakt_*.py`) - Watchlist synchronization
- **Version Management** (`test_version.py`) - Dynamic versioning system

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install -e ".[dev]"

# Ensure FFmpeg is available for integration tests
ffmpeg -version
```

### Basic Test Execution

```bash
# Run all tests
python3 tests/run_tests.py

# Run tests with make (if available)
make test

# Run specific test file
python3 -m unittest tests.test_cli_handler -v

# Run specific test class
python3 -m unittest tests.test_utils.TestCountAllVideoFiles -v
```

### Test Categories

```bash
# Unit tests only (fast)
python3 -m unittest discover tests/ -p "test_*.py" -v

# Integration tests only (slower, requires FFmpeg)
python3 -m unittest discover tests/ -p "*_integration.py" -v

# End-to-end tests (complete workflows)
python3 -m unittest discover tests/ -p "*end_to_end*.py" -v
```

### Test Markers and Filtering

Some tests are marked with special requirements:

```bash
# Tests requiring FFmpeg
python3 -m unittest tests.test_video_inspector_integration -v

# Tests requiring network access (Trakt integration)
python3 -m unittest tests.test_trakt_watchlist -v

# Quick tests only (exclude slow integration tests)
# Use test runner with appropriate filtering
```

## Test Design Principles

### Isolation and Independence
- Each test is completely independent
- No shared state between tests
- Proper setup and teardown for each test
- Temporary files and directories for file system tests

### Comprehensive Coverage
- **Happy path testing**: Normal operation scenarios
- **Edge case testing**: Boundary conditions and unusual inputs
- **Error handling**: Exception scenarios and recovery
- **Input validation**: Parameter checking and sanitization

### Mocking Strategy
- **External dependencies**: Mock FFmpeg execution, file system operations
- **Network calls**: Mock Trakt API interactions
- **System resources**: Mock hardware and environment conditions
- **Strategic real testing**: Use real operations for integration validation

## Test Fixtures

### Video Test Files
```
tests/fixtures/test-videos/
├── corrupt/              # Known corrupt video files
│   ├── frame_corruption.mp4
│   ├── stream_error.mkv
│   └── truncated.avi
└── healthy/              # Known healthy video files
    ├── sample.mp4
    ├── test_video.mkv
    └── reference.avi
```

### Mock Data
- Predefined scan results for testing report generation
- Sample configuration files for validation testing
- Mock Trakt API responses for integration testing

## Key Test Areas

### Video Corruption Detection
- **Pattern recognition**: Test known corruption signatures
- **False positive prevention**: Ensure healthy files aren't flagged
- **Confidence scoring**: Validate corruption probability calculations
- **Timeout handling**: Test behavior with long-running analyses

### CLI Interface
- **Argument parsing**: Validate command-line option handling
- **Error reporting**: Test user-friendly error messages
- **Output formatting**: Verify multiple output format support
- **Signal handling**: Test graceful shutdown and resume

### Configuration System
- **Multi-source loading**: Environment variables, files, secrets
- **Precedence handling**: Correct override behavior
- **Validation**: Invalid configuration detection
- **Default values**: Fallback behavior testing

### Report Generation
- **Multiple formats**: JSON, CSV, YAML, text output
- **Data accuracy**: Correct statistics and metrics
- **Large datasets**: Performance with many files
- **Error conditions**: Handling of incomplete data

### Trakt Integration
- **Authentication**: Token validation and refresh
- **API communication**: Request/response handling
- **Rate limiting**: Respect for API limits
- **Error recovery**: Network failure handling

## Performance Testing

### Load Testing
- **Large directories**: Thousands of video files
- **Memory usage**: Bounded memory consumption
- **Parallel processing**: Multi-threaded scanning efficiency
- **Resume capability**: Recovery from interruption

### Benchmarking
- **Scan performance**: Files processed per second
- **Memory efficiency**: Peak memory usage tracking
- **I/O performance**: File system operation efficiency

## Continuous Integration

### CI/CD Compatibility
- **Exit codes**: Proper success/failure reporting
- **Environment requirements**: Minimal external dependencies
- **Platform support**: Cross-platform test execution
- **Parallel execution**: Safe concurrent test runs

### Docker Testing
```bash
# Run tests in container
docker run --rm -v $(pwd):/app -w /app python:3.11 \
  bash -c "pip install -e .[dev] && python3 tests/run_tests.py"

# Integration with docker-compose
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Adding New Tests

### Unit Test Guidelines
1. **Test one thing**: Each test should verify a single behavior
2. **Descriptive names**: Test names should describe what is being tested
3. **Arrange-Act-Assert**: Clear test structure
4. **Mock external dependencies**: Keep tests fast and reliable

### Integration Test Guidelines
1. **Realistic scenarios**: Test actual user workflows
2. **Real data**: Use actual files and realistic inputs when possible
3. **Error conditions**: Test failure scenarios and recovery
4. **Performance awareness**: Consider test execution time

### Example Test Structure
```python
class TestVideoInspection(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.sample_video = Path(self.temp_dir) / "test.mp4"
        
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_healthy_video_detection(self):
        """Test that healthy videos are correctly identified"""
        # Arrange
        create_sample_video(self.sample_video)
        
        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            result = inspect_video(self.sample_video)
        
        # Assert
        self.assertFalse(result.is_corrupt)
        self.assertLess(result.confidence, 0.1)
```

## Test Statistics and Coverage

- **Total Tests**: 100+ comprehensive tests
- **Unit Tests**: ~70% of test suite (fast execution)
- **Integration Tests**: ~30% of test suite (thorough validation)
- **Code Coverage**: Comprehensive coverage of all public APIs
- **Execution Time**: Unit tests < 10 seconds, full suite < 2 minutes

## Troubleshooting Tests

### Common Issues
1. **FFmpeg not found**: Install FFmpeg for integration tests
2. **Permission errors**: Ensure write access to temp directories
3. **Network timeouts**: Check internet connectivity for Trakt tests
4. **File system limitations**: Some tests require specific file system features

### Debug Mode
```bash
# Run tests with verbose output
python3 tests/run_tests.py --verbose

# Run single test with detailed logging
python3 -m unittest tests.test_video_inspector.TestFFmpegDetection.test_auto_detect -v
```

## Dependencies

### Testing Framework
- **unittest**: Python standard library testing framework
- **unittest.mock**: Mocking and patching functionality
- **tempfile**: Temporary file and directory management

### Test Utilities
- **pathlib**: Cross-platform path handling
- **shutil**: File operations for test cleanup
- **subprocess**: External command execution (mocked in unit tests)

### Optional Dependencies
- **FFmpeg**: Required for integration tests (not unit tests)
- **Network access**: Required for Trakt integration tests
