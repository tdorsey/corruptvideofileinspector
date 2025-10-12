# Nx Monorepo Setup

This document describes the Nx monorepo configuration for the Corrupt Video Inspector project.

## Overview

The repository has been migrated to use Nx for workspace orchestration, computation caching, and intelligent CI/CD workflows. Nx provides:

- **Computation Caching**: Tasks are cached locally and can be shared across CI runs
- **Affected Detection**: Only build/test/lint changed projects (when properly configured)
- **Task Orchestration**: Automatic dependency management and parallel execution
- **Workspace Structure**: Organized apps and shared libraries

## Workspace Structure

```
.
├── apps/
│   ├── cli/              # Python CLI application (main app)
│   ├── api/              # Python API placeholder
│   └── web/              # React + Vite web app placeholder
├── libs/
│   ├── core/             # Shared Python business logic
│   └── ui-components/    # Shared React UI components
├── nx.json               # Nx workspace configuration
├── package.json          # Node.js dependencies and scripts
└── .github/workflows/
    └── ci.yml            # CI/CD pipeline with Nx caching
```

## Projects

### Applications

#### `apps/cli` - Python CLI Application
The main command-line interface for video corruption detection. 

**Note**: The actual source code remains in the root `src/` directory to maintain compatibility with existing tooling. The `apps/cli` directory contains project configuration and references the root source.

**Available Commands**:
```bash
# These commands currently use Make targets for consistency
# with existing development workflow
npm run build          # Build all projects
npm run test           # Run all tests
npm run lint           # Lint all projects
```

#### `apps/api` - Python API (Placeholder)
Future REST API for programmatic access to video corruption detection.

**Status**: Placeholder - implementation pending

#### `apps/web` - React Web UI (Placeholder)
Future browser-based interface for video corruption detection.

**Technology**: React 18 + Vite + TypeScript
**Status**: Placeholder - implementation pending

### Libraries

#### `libs/core` - Core Business Logic
Shared Python modules containing core functionality:
- Video scanning and inspection
- Corruption detection algorithms
- FFmpeg integration
- Data models

**Note**: Source code is located at `src/core/` in the repository root.

#### `libs/ui-components` - UI Components (Placeholder)
Shared React components for web interfaces.

**Status**: Placeholder - implementation pending

## Using Nx

### Installation

Nx and plugins are installed via npm:

```bash
npm install
```

### Common Commands

```bash
# Show all projects in workspace
npx nx show projects

# Run target for specific project
npx nx run <project>:<target>

# Run target for all projects
npx nx run-many --target=<target> --all

# Run target in parallel with custom configuration
npx nx run-many --target=test --all --parallel=3

# Show dependency graph
npx nx graph

# Clear Nx cache
npx nx reset
```

### Current Implementation Notes

The current setup uses standard Make targets wrapped by Nx for the CLI project:

```bash
# These are equivalent:
make test
npx nx run cli:test

# All projects:
npm test  # runs: nx run-many --target=test --all
```

### Affected Commands

Nx can detect which projects are affected by changes and only run tasks for those projects:

```bash
# Test only affected projects
npx nx affected --target=test

# Build only affected projects
npx nx affected --target=build

# Lint only affected projects
npx nx affected --target=lint
```

**Note**: Affected detection requires a base branch (typically `main`) to compare against.

## CI/CD Integration

The `.github/workflows/ci.yml` workflow integrates Nx for intelligent CI/CD:

### Features

1. **Nx Computation Cache**: Results are cached in `.nx/cache` and restored across CI runs
2. **Parallel Execution**: Multiple jobs run in parallel where possible
3. **Docker Layer Caching**: Docker builds leverage layer caching
4. **Dependency-based Orchestration**: Jobs run in optimal order based on dependencies

### Workflow Stages

1. **Setup**: Install dependencies, restore caches
2. **Lint & Format**: Code quality checks with caching
3. **Security**: Security scans
4. **Test**: Run test suite with caching
5. **Docker Build**: Build and test Docker images with layer caching

### Cache Strategy

- **Nx Cache**: Stores task outputs (test results, lint results, etc.)
  - Key: `nx-cache-${{ runner.os }}-${{ hashFiles('**/package-lock.json', '**/pyproject.toml') }}`
  - Location: `.nx/cache`

- **Docker Cache**: Stores Docker build layers
  - Key: `${{ runner.os }}-buildx-${{ hashFiles('**/Dockerfile', '**/pyproject.toml') }}`
  - Location: `/tmp/.buildx-cache`

- **npm Cache**: Node.js dependencies
  - Managed by `actions/setup-node` with `cache: 'npm'`

- **pip Cache**: Python dependencies
  - Managed by `actions/setup-python` with `cache: 'pip'`

## Configuration Files

### `nx.json`

Main Nx workspace configuration:

```json
{
  "$schema": "./node_modules/nx/schemas/nx-schema.json",
  "defaultBase": "main",
  "targetDefaults": {
    "build": {
      "cache": true
    },
    "test": {
      "cache": true
    },
    "lint": {
      "cache": true
    }
  },
  "cacheDirectory": ".nx/cache"
}
```

### `<project>/project.json`

Each project has a `project.json` defining its targets:

```json
{
  "name": "cli",
  "targets": {
    "test": {
      "executor": "nx:run-commands",
      "options": {
        "command": "make test",
        "cwd": "{workspaceRoot}"
      }
    }
  }
}
```

## Development Workflow

### Local Development

1. **Install dependencies**:
   ```bash
   npm install
   make install-dev
   ```

2. **Run tests**:
   ```bash
   npm test  # All projects
   make test # CLI project specifically
   ```

3. **Lint code**:
   ```bash
   npm run lint
   ```

4. **View dependency graph**:
   ```bash
   npm run graph
   ```

### Working with Nx Cache

Nx caches task outputs to speed up repeated operations:

```bash
# First run - executes and caches
npm test

# Second run - retrieves from cache (much faster)
npm test

# Clear cache if needed
npx nx reset
```

### CI/CD Testing

To test CI/CD workflows locally:

```bash
# Install act (GitHub Actions local runner)
# https://github.com/nektos/act

# Run workflow
act -j setup
act -j lint-and-format
act -j test
```

## Extending the Monorepo

### Adding a New Application

1. Create directory structure:
   ```bash
   mkdir -p apps/new-app/src
   ```

2. Create `apps/new-app/project.json`:
   ```json
   {
     "name": "new-app",
     "projectType": "application",
     "sourceRoot": "apps/new-app/src",
     "targets": {
       "build": {
         "executor": "nx:run-commands",
         "options": {
           "command": "echo 'Build new-app'"
         }
       }
     }
   }
   ```

3. Reset Nx cache:
   ```bash
   npx nx reset
   ```

### Adding a New Library

Same as adding an application, but set `"projectType": "library"` and place in `libs/` directory.

### Setting Up Dependencies

Use the `implicitDependencies` or `dependsOn` in project.json to define relationships:

```json
{
  "name": "api",
  "implicitDependencies": ["core"]
}
```

## Troubleshooting

### Projects Not Detected

If `npx nx show projects` returns empty:

1. Verify `project.json` exists in project directory
2. Check JSON syntax is valid
3. Reset Nx daemon: `npx nx daemon --stop && npx nx reset`
4. Ensure project directory is in `apps/` or `libs/`

### Cache Issues

If cached results are stale or incorrect:

```bash
# Clear all caches
npx nx reset

# Clear specific target cache
npx nx reset --target=test
```

### CI Cache Not Restoring

Check that:
1. Cache key matches between save and restore steps
2. `.nx/cache` directory is included in cache path
3. Dependencies (package-lock.json, pyproject.toml) haven't changed

## Future Enhancements

Planned improvements for the Nx integration:

1. **Project Auto-Discovery**: Resolve project detection issues for seamless Nx commands
2. **Nx Cloud Integration**: Optional remote caching for distributed teams
3. **Affected-Based Testing**: Implement proper affected detection in CI
4. **API Implementation**: Build out the Python API with Nx orchestration
5. **Web UI Implementation**: Complete React+Vite web interface
6. **Shared Libraries**: Extract common code to shared libraries
7. **Release Automation**: Use Nx release tools for version management

## References

- [Nx Documentation](https://nx.dev)
- [Nx Python Plugin (@nxlv/python)](https://github.com/lucasvieirasilva/nx-plugins)
- [Nx Affected Commands](https://nx.dev/concepts/affected)
- [Nx Caching](https://nx.dev/concepts/how-caching-works)
- [GitHub Actions Caching](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
