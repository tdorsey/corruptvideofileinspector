# Nx Monorepo Quick Start

This repository uses Nx for workspace orchestration and caching with pnpm workspaces. This guide provides quick reference commands for common tasks.

## Prerequisites

```bash
# Install pnpm (if not already installed)
npm install -g pnpm

# Install Node.js dependencies
pnpm install

# Install Python dependencies
make install-dev
```

## Quick Commands

### Running Tasks

```bash
# Run tests for all projects
pnpm test

# Run lint for all projects
pnpm run lint

# Run build for all projects
pnpm run build

# Format code
pnpm run format
```

### Nx-Specific Commands

```bash
# Show all projects
pnpm nx show projects

# Run specific target for a project
pnpm nx run <project>:<target>

# Example: Run CLI tests
pnpm nx run cli:test

# Run target for all projects in parallel
pnpm nx run-many --target=<target> --all --parallel=3
```

### Affected Commands

```bash
# Test only changed projects
pnpm nx affected --target=test

# Build only changed projects
pnpm nx affected --target=build

# Show what would be affected
pnpm nx affected:graph
```

### Workspace Commands

```bash
# View dependency graph (opens in browser)
pnpm run graph

# Clear Nx cache
pnpm nx reset

# Show Nx configuration
pnpm nx report
```

## Project Structure

```
apps/
  cli/          - Python CLI (main application)
  api/          - Python API (placeholder)
  web/          - React web UI (placeholder)

libs/
  core/         - Shared Python logic
  ui-components/- Shared React components
```

## Available Projects

- **cli**: Python command-line interface
- **api**: REST API (placeholder)
- **web**: Web interface (placeholder)
- **core**: Shared Python libraries
- **ui-components**: Shared UI components (placeholder)

## Caching

Nx caches task results to speed up repeated operations:

- First run: Executes tasks and caches results
- Subsequent runs: Retrieves from cache (much faster)
- Cache location: `.nx/cache/`

To clear cache: `npx nx reset`

## CI/CD

The repository uses Nx-powered CI/CD in `.github/workflows/ci.yml`:

- ✅ Intelligent caching across CI runs
- ✅ Parallel job execution
- ✅ Docker layer caching
- ✅ Dependency-based workflow orchestration

## Documentation

For detailed information, see:
- [`docs/NX_MONOREPO.md`](docs/NX_MONOREPO.md) - Complete Nx setup documentation
- [`README.md`](README.md) - Main project README
- [Nx Documentation](https://nx.dev)

## Troubleshooting

**Projects not showing?**
```bash
pnpm nx daemon --stop
pnpm nx reset
```

**Cache issues?**
```bash
pnpm nx reset
```

**Need help?**
```bash
pnpm nx help
pnpm nx list  # Show installed plugins
```
