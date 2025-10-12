# Corrupt Video Inspector CLI

Python command-line application for detecting corrupted video files using FFmpeg.

## Overview

This application provides a CLI interface for scanning video files and detecting corruption issues. It integrates with Trakt.tv for watchlist synchronization.

## Source Code

The source code for this application is located in the `src/` directory at the root of the monorepo. This follows the existing project structure.

## Running the CLI

```bash
# Using Nx
nx run cli

# Direct execution
python cli_handler.py --help
```

## Development Commands

```bash
# Run tests
nx test cli

# Run unit tests only
nx run cli:test-unit

# Lint code
nx lint cli

# Format code
nx format cli

# Type check
nx run cli:type-check
```

## Build

```bash
nx build cli
```

## Dependencies

See `../../pyproject.toml` for Python dependencies.
