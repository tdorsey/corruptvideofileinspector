#!/usr/bin/env python3
"""
CLI handler for corrupt-video-inspector package.

This module provides the main entry point for the corrupt-video-inspector
command-line interface as specified in pyproject.toml.
"""

import sys
from src.cli.main import main as cli_main_func


def main():
    """Entry point for the corrupt-video-inspector CLI command."""
    return cli_main_func()


if __name__ == "__main__":
    sys.exit(main())
