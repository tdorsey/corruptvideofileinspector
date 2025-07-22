# Integration Testing for Corrupt Video Inspector

This directory contains comprehensive integration tests for the Corrupt Video Inspector application.

## Overview

The integration tests validate the end-to-end functionality of the application, ensuring that all components work together correctly. The tests are built using Python's built-in `unittest` framework for maximum compatibility.

## Test Structure

```
tests/
├── __init__.py                        # Test package initialization
├── run_tests.py                       # Test runner script
├── test_utils_integration.py          # Tests for utils module
├── test_video_inspector_integration.py # Tests for video_inspector module
├── test_cli_integration.py            # Tests for CLI functionality
├── test_end_to_end_integration.py     # End-to-end workflow tests
└── README.md                          # This file
```

## Test Categories

### 1. Utils Integration Tests (`test_utils_integration.py`)
- File counting functionality
- File size formatting
- Video extension handling
- Directory scanning (recursive/non-recursive)
- Case-insensitive file matching
- Error handling for invalid directories

### 2. Video Inspector Integration Tests (`test_video_inspector_integration.py`)
- VideoFile object creation and management
- VideoInspectionResult object functionality
- Video file discovery
- FFmpeg command detection
- Scan mode enumeration
- JSON serialization/deserialization

### 3. CLI Integration Tests (`test_cli_integration.py`)
- CLI function validation
- Logging configuration
- Directory validation logic
- Integration between CLI and core modules
- Argument validation patterns

### 4. End-to-End Integration Tests (`test_end_to_end_integration.py`)
- Complete video discovery workflow
- Multi-module integration
- Large directory structure handling
- Recursive vs non-recursive consistency
- Extension filtering workflows
- Performance simulation tests

## Running Tests

### Run All Tests
```bash
# Using make (recommended)
make test

# Or directly
python3 tests/run_tests.py
```

### Run Specific Test Module
```bash
# Run utils tests only
python3 tests/run_tests.py utils_integration

# Run video inspector tests only
python3 tests/run_tests.py video_inspector_integration

# Run CLI tests only
python3 tests/run_tests.py cli_integration

# Run end-to-end tests only
python3 tests/run_tests.py end_to_end_integration
```

### Run Individual Test Methods
```bash
# Run specific test class
python3 -m unittest tests.test_utils_integration.TestUtilsIntegration -v

# Run specific test method
python3 -m unittest tests.test_utils_integration.TestUtilsIntegration.test_count_video_files_with_video_files -v
```

## Test Features

### Automatic Test Discovery
The test runner automatically discovers all `test_*.py` files in the tests directory and runs them.

### Comprehensive Coverage
- **37 integration tests** covering all major functionality
- Tests for both success and error scenarios
- Edge cases and boundary conditions
- Large-scale performance simulations

### Isolated Test Environment
- Each test uses temporary directories and files
- Automatic cleanup after each test
- No dependencies on external files or services
- No modification of existing project files

### Real-World Scenarios
- Tests use realistic directory structures
- Multiple file types and extensions
- Nested directory hierarchies
- Large-scale directory simulations

## Test Data

Tests create their own temporary test data including:
- Video files with various extensions (.mp4, .avi, .mkv, .mov, etc.)
- Non-video files for filtering tests
- Nested directory structures
- Empty directories
- Files with different sizes and content

## Dependencies

The integration tests use only Python standard library modules:
- `unittest` - Test framework
- `tempfile` - Temporary file/directory creation
- `os` / `pathlib` - File system operations
- `sys` - System-specific parameters

No external testing dependencies (like pytest) are required, ensuring maximum compatibility.

## Test Output

The test runner provides:
- Verbose output showing each test as it runs
- Summary statistics (tests run, failures, errors, skipped)
- Detailed failure/error reporting
- Clear indication of test results

Example output:
```
============================================================
INTEGRATION TEST SUMMARY
============================================================
Tests run: 37
Failures: 0
Errors: 0
Skipped: 0

All tests passed!
```

## Adding New Tests

To add new integration tests:

1. Create a new test file following the naming pattern `test_*_integration.py`
2. Import required modules and set up the test class
3. Use `setUp()` and `tearDown()` methods for test isolation
4. Write test methods following the pattern `test_*`
5. Use descriptive test names and docstrings
6. Clean up any resources in `tearDown()`

Example test structure:
```python
import unittest
import tempfile
import os

class TestNewFeatureIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        # Clean up code here
        
    def test_new_feature_functionality(self):
        """Test description"""
        # Test implementation here
        
if __name__ == '__main__':
    unittest.main()
```

## Continuous Integration

These tests are designed to run in any Python 3.8+ environment and can be easily integrated into CI/CD pipelines:

```bash
# In CI script
make test
```

The tests will exit with code 0 on success and non-zero on failure, making them suitable for automated testing environments.