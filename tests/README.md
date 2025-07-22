# Unit Tests for Corrupt Video Inspector

This directory contains comprehensive unit tests for all functions in the Corrupt Video Inspector project.

## Test Structure

### Test Files

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
  - `validate_directory()` - Directory validation
  - `parse_cli_arguments()` - Argument parsing
  - `validate_arguments()` - Argument validation
  - `list_video_files()` - File listing functionality
  - `check_system_requirements()` - System dependency checks
  - `main()` - Main CLI entry point

### Test Coverage

The test suite provides comprehensive coverage including:

- **Normal operation cases** - Testing expected functionality
- **Edge cases** - Boundary conditions and unusual inputs
- **Error conditions** - Exception handling and error scenarios
- **Input validation** - Parameter checking and validation
- **External dependency mocking** - Mocking ffmpeg calls and file system operations

## Running Tests

### Run All Tests
```bash
# Using the test runner (recommended)
python3 tests/run_tests.py

# Using unittest directly
python3 -m unittest discover tests/ -v
```

### Run Individual Test Files
```bash
# Test utilities
python3 -m unittest tests.test_utils -v

# Test video inspector
python3 -m unittest tests.test_video_inspector -v

# Test CLI handler
python3 -m unittest tests.test_cli_handler -v
```

### Run Specific Test Classes
```bash
# Test video file counting
python3 -m unittest tests.test_utils.TestCountAllVideoFiles -v

# Test FFmpeg detection
python3 -m unittest tests.test_video_inspector.TestGetFfmpegCommand -v

# Test argument parsing
python3 -m unittest tests.test_cli_handler.TestParseCliArguments -v
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

- **Total Tests**: 71
- **Test Files**: 3
- **Functions Tested**: 16
- **Classes Tested**: 3
- **Code Coverage**: Comprehensive coverage of all public functions

## Dependencies

The tests use only Python standard library modules:
- `unittest` - Core testing framework
- `unittest.mock` - Mocking functionality
- `tempfile` - Temporary file/directory creation
- `pathlib` - Path operations
- Standard library modules for specific functionality

No external testing dependencies are required, keeping the test suite lightweight and self-contained.