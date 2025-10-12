# UI Components Library

Shared React components for web interfaces (placeholder).

## Overview

This library will contain reusable React components used across web applications.

## Planned Components

- File upload widgets
- Progress indicators
- Results tables and visualizations
- Status badges
- Navigation components

## Technology Stack

- React 18+
- TypeScript
- CSS/styled-components (TBD)

## Usage

```typescript
import { FileUploader, ProgressBar } from '@corruptvideofileinspector/ui-components';
```

## Development Commands

> ⚠️ **Note:** These Nx targets may not resolve until project discovery is fixed. If you encounter errors running these commands, please check your Nx workspace configuration and ensure project discovery is working.
```bash
# Build library
nx build ui-components

# Run tests
nx test ui-components

# Lint code
nx lint ui-components
```

## Consumers

This library will be consumed by:
- Web application (`apps/web`)
- Future web-based tools
