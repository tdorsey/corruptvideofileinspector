"""
Main entry point for the Corrupt Video Inspector application.

This module allows the package to be executed as:
    python -m corrupt_video_inspector
"""

from .cli.commands import cli

def main():
    """Main entry point for CLI application."""
    cli()

if __name__ == "__main__":
    main()
