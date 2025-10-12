# Nx Monorepo Quick Start

This repository uses Nx for workspace orchestration and caching. This guide provides quick reference commands for common tasks.

## Prerequisites

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
make install-dev
```

## Quick Commands

### Running Tasks

```bash
# Run tests for all projects
npm test

# Run lint for all projects
npm run lint

# Run build for all projects
npm run build

# Format code
npm run format
```

### Nx-Specific Commands

```bash
# Show all projects
npx nx show projects

# Run specific target for a project
npx nx run <project>:<target>

# Example: Run CLI tests
npx nx run cli:test

# Run target for all projects in parallel
npx nx run-many --target=<target> --all --parallel=3
```

### Affected Commands

```bash
# Test only changed projects
npx nx affected --target=test

# Build only changed projects
npx nx affected --target=build

# Show what would be affected
npx nx affected:graph
```

### Workspace Commands

```bash
# View dependency graph (opens in browser)
npm run graph

# Clear Nx cache
npx nx reset

# Show Nx configuration
npx nx report
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
npx nx daemon --stop
npx nx reset
```

**Cache issues?**
```bash
npx nx reset
```

**Need help?**
```bash
npx nx help
npx nx list  # Show installed plugins
```
