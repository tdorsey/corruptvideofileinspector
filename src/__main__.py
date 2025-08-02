"""
Main entry point for the Corrupt Video Inspector application.

This module allows the package to be executed as:
    python -m src.main
    python src/main.py
"""

from .cli.main import cli

if __name__ == "__main__":
    cli()
