#!/usr/bin/env python3
"""
Corrupt Video Inspector - Main entry point
A tool to scan directories for corrupt video files using ffmpeg.

Refactored to follow Single Responsibility Principle (SRP) and DRY principles.
Separated into multiple modules for better maintainability and testability.
"""
import sys
from cli_handler import parse_cli_arguments, run_cli_mode
from gui_handler import run_gui_mode


def main():
    """Main entry point for the Corrupt Video Inspector application"""
    try:
        # Parse command line arguments
        args = parse_cli_arguments()
        
        # If directory is provided, run in CLI mode
        if args.directory:
            run_cli_mode(args)
        else:
            # Run in GUI mode
            success = run_gui_mode()
            if not success:
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()