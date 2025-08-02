#!/usr/bin/env python3
"""
Demo script to show dynamic versioning functionality.

This script demonstrates how the Poetry dynamic versioning works
by showing the version retrieved through different methods.
"""

import subprocess
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.version import __version__, get_version
    from src import __version__ as package_version
    
    print("=== Poetry Dynamic Versioning Demo ===")
    print()
    
    # Show git information
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--dirty"], 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        if result.returncode == 0:
            git_version = result.stdout.strip()
            print(f"Git describe: {git_version}")
        else:
            print("Git describe: No tags found")
    except Exception as e:
        print(f"Git error: {e}")
    
    print()
    print("=== Version Information ===")
    print(f"Direct import from version.py: {__version__}")
    print(f"get_version() function: {get_version()}")
    print(f"Package __version__: {package_version}")
    print()
    
    # Show expected behavior
    print("=== Expected Behavior ===")
    print("When not installed: Returns fallback '0.0.0+dev'")
    print("When installed with exact tag: Returns tag version (e.g., '1.0.0')")
    print("When installed with commits after tag: Returns development version")
    print("  (e.g., '1.0.1.dev1+g<commit-hash>')")
    
except Exception as e:
    print(f"Error demonstrating versioning: {e}")
    import traceback
    traceback.print_exc()