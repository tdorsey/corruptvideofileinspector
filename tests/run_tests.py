#!/usr/bin/env python3
"""
Test runner for Corrupt Video Inspector integration tests
"""
import sys
import unittest
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def discover_and_run_tests():
    """Discover and run all integration tests"""
    # Set up test discovery
    test_dir = os.path.dirname(os.path.abspath(__file__))
    loader = unittest.TestLoader()
    
    # Discover all test files in the tests directory
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print(f"\nFAILED TESTS:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\nERROR TESTS:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.skipped:
        print(f"\nSKIPPED TESTS:")
        for test, reason in result.skipped:
            print(f"  - {test}: {reason}")
    
    # Return exit code
    if result.failures or result.errors:
        print(f"\nSome tests failed!")
        return 1
    else:
        print(f"\nAll tests passed!")
        return 0


def run_specific_test_module(module_name):
    """Run tests from a specific module"""
    try:
        # Import the test module
        module = __import__(f'tests.{module_name}', fromlist=['tests'])
        
        # Create test suite from the module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
        
    except ImportError as e:
        print(f"Error importing test module '{module_name}': {e}")
        return 1


def main():
    """Main test runner entry point"""
    if len(sys.argv) > 1:
        # Run specific test module
        module_name = sys.argv[1]
        if module_name.startswith('test_'):
            module_name = module_name[:-3] if module_name.endswith('.py') else module_name
        else:
            module_name = f'test_{module_name}'
        
        print(f"Running tests from module: {module_name}")
        return run_specific_test_module(module_name)
    else:
        # Run all tests
        print("Running all integration tests...")
        return discover_and_run_tests()


if __name__ == '__main__':
    sys.exit(main())