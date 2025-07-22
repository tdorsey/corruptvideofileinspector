#!/usr/bin/env python3
"""
Unified test runner for Corrupt Video Inspector
Runs both unit tests and integration tests with comprehensive reporting
"""

import os
import sys
import unittest

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def discover_and_run_tests(pattern="test_*.py"):
    """Discover and run tests with the specified pattern"""
    # Set up test discovery
    test_dir = os.path.dirname(os.path.abspath(__file__))
    loader = unittest.TestLoader()

    # Discover all test files in the tests directory
    suite = loader.discover(test_dir, pattern=pattern)

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    return runner.run(suite)


def run_specific_test_module(module_name):
    """Run tests from a specific module"""
    try:
        # Import the test module
        module = __import__(f"tests.{module_name}", fromlist=["tests"])

        # Create test suite from the module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)

        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)

    except ImportError as e:
        print(f"Error importing test module '{module_name}': {e}")
        return None


def print_summary(result, test_type="ALL"):
    """Print test summary"""
    print("\n" + "=" * 60)
    print(f"{test_type} TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.failures:
        print("\nFAILED TESTS:")
        for test, _traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\nERROR TESTS:")
        for test, _traceback in result.errors:
            print(f"  - {test}")

    if result.skipped:
        print("\nSKIPPED TESTS:")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")

    # Success message
    if result.failures or result.errors:
        print("\n❌ Some tests failed!")
        return False
    print("\n✅ All tests passed!")
    return True


def main():
    """Main test runner entry point"""
    if len(sys.argv) > 1:
        # Run specific test module or type
        arg = sys.argv[1].lower()

        if arg == "unit":
            # Run only unit tests (exclude integration tests)
            print("Running unit tests only...")
            result = discover_and_run_tests("test_[!*integration]*.py")
            success = print_summary(result, "UNIT")

        elif arg == "integration":
            # Run only integration tests
            print("Running integration tests only...")
            result = discover_and_run_tests("test_*integration*.py")
            success = print_summary(result, "INTEGRATION")

        else:
            # Run specific test module
            module_name = arg
            if module_name.startswith("test_"):
                module_name = module_name[:-3] if module_name.endswith(".py") else module_name
            else:
                module_name = f"test_{module_name}"

            print(f"Running tests from module: {module_name}")
            result = run_specific_test_module(module_name)

            if result is None:
                return 1

            success = print_summary(result, f"MODULE ({module_name})")

    else:
        # Run all tests
        print("Running all tests (unit + integration)...")
        result = discover_and_run_tests()
        success = print_summary(result, "ALL")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
