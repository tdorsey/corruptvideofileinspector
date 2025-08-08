# Testing Suite for Corrupt Video Inspector

This directory contains comprehensive testing coverage for the Corrupt Video Inspector project, including both unit tests and integration tests.

## Test Types

### Unit Tests
Fast, isolated tests that verify individual functions and components:

- **`test_utils.py`** - Tests for utility functions in `utils.py`
  - `count_all_video_files()` - File counting with various options
  - `format_file_size()` - Human-readable file size formatting
  - `get_video_extensions()` - Supported video file extensions

- **`test_video_inspector.py`** - Tests for core video inspection functionality in `video_inspector.py`
  - `get_ffmpeg_command()` - FFmpeg command detection
  - `get_all_video_object_files()` - Video file discovery
  - `inspect_single_video_quick()` - Quick video inspection
  - `inspect_single_video_deep()` - Deep video inspection
  - `inspect_single_video()` - Inspection mode wrapper
  - `inspect_video_files_cli()` - CLI inspection interface
  - Classes: `VideoFile`, `VideoInspectionResult`, `ScanMode`

- **`test_cli_handler.py`** - Tests for command-line interface in `cli_handler.py`
  - `setup_logging()` - Logging configuration
  - `parse_cli_arguments()` - Argument parsing
  - `list_video_files()` - File listing functionality
  - `check_system_requirements()` - System dependency checks
  - `main()` - Main CLI entry point

### Integration Tests
End-to-end tests that validate complete workflows and component interactions:

- **`test_utils_integration.py`** - Utils module integration tests
- **`test_video_inspector_integration.py`** - Video inspector integration tests
- **`test_cli_integration.py`** - CLI functionality integration tests
- **`test_end_to_end_integration.py`** - Complete workflow integration tests

## Test Coverage

The test suite provides comprehensive coverage including:

- **Normal operation cases** - Testing expected functionality
- **Edge cases** - Boundary conditions and unusual inputs
- **Error conditions** - Exception handling and error scenarios
- **Input validation** - Parameter checking and validation
- **External dependency mocking** - Mocking ffmpeg calls and file system operations
- **End-to-end workflows** - Complete application scenarios

## Running Tests

### Run All Tests
```bash
# Using the test runner (recommended)
python3 tests/run_tests.py

# Using make (if available)
make test

# Using unittest directly
python3 -m unittest discover tests/ -v
```

### Run Unit Tests Only
```bash
# Test utilities
python3 -m unittest tests.test_utils -v

# Test video inspector
python3 -m unittest tests.test_video_inspector -v

# Test CLI handler
python3 -m unittest tests.test_cli_handler -v
```

### Run Integration Tests Only
```bash
# Run utils integration tests
python3 tests/run_tests.py test_utils_integration

# Run video inspector integration tests
python3 tests/run_tests.py test_video_inspector_integration

# Run CLI integration tests
python3 tests/run_tests.py test_cli_integration

# Run end-to-end integration tests
python3 tests/run_tests.py test_end_to_end_integration
```

### Run Specific Test Classes
```bash
# Test video file counting (unit test)
python3 -m unittest tests.test_utils.TestCountAllVideoFiles -v

# Test FFmpeg detection (unit test)
python3 -m unittest tests.test_video_inspector.TestGetFfmpegCommand -v

# Test argument parsing (unit test)
python3 -m unittest tests.test_cli_handler.TestParseCliArguments -v

# Test utils integration
python3 -m unittest tests.test_utils_integration.TestUtilsIntegration -v
```

## Test Design Principles

### Isolation
- Each test is independent and doesn't rely on other tests
- Test fixtures are created and cleaned up for each test
- Temporary files and directories are used to avoid side effects

### Mocking
- External dependencies (subprocess calls, file system operations) are mocked
- Mocking is used strategically to test logic without external dependencies
- Real file system operations are tested when appropriate for integration testing

### Comprehensive Coverage
- Tests cover both success and failure scenarios
- Edge cases and boundary conditions are thoroughly tested
- Error handling and exception scenarios are validated

## Test Statistics

- **Unit Tests**: 71 tests across 3 test modules
- **Integration Tests**: 37 tests across 4 test modules
- **Total Tests**: 108+ comprehensive tests
- **Functions Tested**: All public functions and classes
- **Code Coverage**: Comprehensive coverage of all functionality

## Dependencies

The tests use only Python standard library modules:
- `unittest` - Core testing framework
- `unittest.mock` - Mocking functionality
- `tempfile` - Temporary file/directory creation
- `pathlib` / `os` - Path and file operations
- Standard library modules for specific functionality

No external testing dependencies are required, keeping the test suite lightweight and self-contained.

## Test Output

The test runner provides:
- Verbose output showing each test as it runs
- Summary statistics (tests run, failures, errors, skipped)
- Detailed failure/error reporting
- Clear indication of test results

## Adding New Tests

### Unit Tests
Create test files following the pattern `test_*.py` (without `_integration` suffix):
- Focus on testing individual functions in isolation
- Use mocking for external dependencies
- Test edge cases and error conditions

### Integration Tests
Create test files following the pattern `test_*_integration.py`:
- Test complete workflows and component interactions
- Use real file system operations where appropriate
- Test realistic scenarios and data flows

## Continuous Integration

These tests are designed to run in any Python 3.13+ environment and can be easily integrated into CI/CD pipelines. The tests will exit with code 0 on success and non-zero on failure, making them suitable for automated testing environments.
