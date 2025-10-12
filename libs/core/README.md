# Core Library

Shared Python business logic for video corruption detection.

## Overview

This library contains the core business logic used across all applications:

- Video scanning and inspection
- Corruption detection algorithms
- File processing utilities
- Data models and schemas
- FFmpeg integration

## Source Code

The source code for this library is located at `../../src/core/` in the monorepo root, maintaining the existing project structure.

## Usage

This library is consumed by:
- CLI application (`apps/cli`)
- API application (`apps/api`)

## Development Commands

```bash
# Run tests
nx test core

# Lint code
nx lint core

# Format code
nx format core

# Type check
nx run core:type-check
```

## Testing

Unit tests are located in `tests/unit/` and can be filtered to test only core functionality.
