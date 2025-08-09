#!/usr/bin/env python3
"""
CLI Handler - Convenience wrapper for the main CLI application.

This module provides a simple entry point that delegates to the main CLI module.
"""

from src.cli.main import main

if __name__ == "__main__":
    # Delegate to the main CLI module
    main()
