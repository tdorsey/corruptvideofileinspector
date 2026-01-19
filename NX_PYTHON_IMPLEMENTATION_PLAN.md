# Nx Python Integration Implementation Plan

## Overview
Configure the Corrupt Video Inspector repository to use AWS Nx plugin for Python, enabling agents and developers to use unified `nx lint`, `nx test`, etc. commands instead of Python-specific commands like `pytest` or `ruff`.

## Background
The repository currently:
- Has Nx installed (`nx.json`, `package.json`) but configured only for basic JavaScript/TypeScript
- Uses Make targets (`make lint`, `make test`) that call Python tools directly (ruff, pytest, black, mypy)
- Has placeholder project structure in `apps/` and `libs/` directories
- Has actual Python source code in root `src/` directory
- Uses GitHub Actions CI/CD that calls Make targets

## Requirements
Per issue #319, we need to:
1. Install and configure AWS Nx plugin for Python support (https://awslabs.github.io/nx-plugin-for-aws/)
2. Configure Python executors for standard targets (lint, test, format, type)
3. Update agents and workflows to use `nx` commands instead of Python tool commands

## Technical Specification

### 1. AWS Nx Plugin Installation

**Package**: `@aws/nx-plugin`

Already installed in `package.json` at version `^0.65.0`.

**Configuration Required**:
- Add plugin to `nx.json` plugins list
- Configure Python-specific settings

### 2. Project Structure Mapping

Current source layout:
```
src/
├── api/          # API implementation
├── cli/          # CLI implementation
├── core/         # Core business logic
├── config/       # Configuration
├── database/     # Database layer
├── ffmpeg/       # FFmpeg integration
├── trakt/        # Trakt integration
└── utils/        # Utilities
```

Nx project mapping:
- `apps/cli` → Uses `src/cli/` and other root `src/` modules
- `apps/api` → Uses `src/api/` and shared modules
- `libs/core` → Uses `src/core/`, `src/config/`, `src/database/`, etc.

### 3. Project Configuration Files

Each project needs a `project.json` file defining:

#### `apps/cli/project.json`
```json
{
  "name": "cli",
  "sourceRoot": "apps/cli/src",
  "projectType": "application",
  "targets": {
    "lint": {
      "executor": "@aws/nx-plugin:python-run-commands",
      "options": {
        "command": "ruff check --fix --unsafe-fixes .",
        "cwd": "{projectRoot}/../.."
      }
    },
    "test": {
      "executor": "@aws/nx-plugin:python-run-commands",
      "options": {
        "command": "pytest tests/ -v -m unit",
        "cwd": "{projectRoot}/../.."
      },
      "cache": true,
      "inputs": ["default", "^default", "{projectRoot}/../../tests/**/*"]
    },
    "format": {
      "executor": "@aws/nx-plugin:python-run-commands",
      "options": {
        "command": "black .",
        "cwd": "{projectRoot}/../.."
      }
    },
    "type": {
      "executor": "@aws/nx-plugin:python-run-commands",
      "options": {
        "command": "mypy .",
        "cwd": "{projectRoot}/../.."
      }
    }
  }
}
```

**Note**: The `cwd` is set to repository root (`{projectRoot}/../..`) because:
- Python source is in root `src/` directory
- Tools (ruff, black, mypy) expect to run from repository root
- Test files are in root `tests/` directory
- Configuration files (pyproject.toml) are in repository root

#### `apps/api/project.json`
Similar structure to CLI, with API-specific test filters.

#### `libs/core/project.json`
Similar structure, but `projectType: "library"` and no application-specific commands.

### 4. Target Definitions

Standard targets to implement across all Python projects:

| Target | Tool | Command | Cache | Description |
|--------|------|---------|-------|-------------|
| `lint` | ruff | `ruff check --fix --unsafe-fixes .` | ✅ | Lint and auto-fix |
| `test` | pytest | `pytest tests/ -v -m unit` | ✅ | Run unit tests |
| `format` | black | `black .` | ✅ | Format code |
| `type` | mypy | `mypy .` | ✅ | Type checking |
| `check` | make | Runs format + lint + type | ✅ | Combined quality check |

### 5. Nx Workspace Configuration Updates

#### `nx.json` additions:
```json
{
  "plugins": [
    "@aws/nx-plugin"
  ],
  "targetDefaults": {
    "lint": {
      "cache": true,
      "inputs": [
        "default",
        "{workspaceRoot}/pyproject.toml",
        "{workspaceRoot}/.ruff.toml"
      ]
    },
    "test": {
      "cache": true,
      "inputs": [
        "default",
        "^default",
        "{workspaceRoot}/pyproject.toml",
        "{workspaceRoot}/pytest.ini"
      ]
    },
    "format": {
      "cache": true,
      "inputs": [
        "default",
        "{workspaceRoot}/pyproject.toml"
      ]
    },
    "type": {
      "cache": true,
      "inputs": [
        "default",
        "{workspaceRoot}/pyproject.toml",
        "{workspaceRoot}/mypy.ini"
      ]
    }
  }
}
```

### 6. Package.json Script Updates

Replace Make-centric scripts with Nx commands:

```json
{
  "scripts": {
    "test": "nx run-many --target=test --all",
    "lint": "nx run-many --target=lint --all",
    "format": "nx run-many --target=format --all",
    "type": "nx run-many --target=type --all",
    "check": "nx run-many --target=lint --all && nx run-many --target=type --all",
    "test:affected": "nx affected --target=test",
    "lint:affected": "nx affected --target=lint",
    "graph": "nx graph"
  }
}
```

### 7. CI/CD Workflow Updates

#### `.github/workflows/ci.yml` changes:

**Current**:
```yaml
- name: Lint and Format
  run: |
    set -e
    make lint

- name: Run Tests
  run: |
    set -e
    make test
```

**New**:
```yaml
- name: Lint and Format
  run: |
    set -e
    npx nx affected --target=lint --base=origin/main

- name: Run Tests
  run: |
    set -e
    npx nx affected --target=test --base=origin/main
```

**Benefits**:
- Only lints/tests changed projects
- Leverages Nx caching for faster CI
- Parallel execution across projects

### 8. Agent Instruction Updates

Files to update with new command patterns:

1. **`.github/instructions/MAIN.md`**
   - Replace `make lint` references with `nx lint <project>` or `nx affected --target=lint`
   - Replace `make test` with `nx test <project>` or `nx affected --target=test`
   - Update "Quick Reference" section

2. **`.github/agents/*.agent.md`**
   - Update tool authority sections to reference nx commands
   - Add examples using `nx` instead of `pytest`, `ruff`, `black` directly

3. **`NX_QUICK_START.md`**
   - Add Python project examples
   - Document nx lint/test/format/type commands
   - Show affected command usage

4. **`docs/NX_MONOREPO.md`**
   - Document Python executor configuration
   - Explain project.json structure for Python projects
   - Add troubleshooting for Python + Nx issues

### 9. Backward Compatibility

**Preserve Makefile** during transition:
- Keep all existing Make targets functional
- Makefile can internally call nx commands
- Allow gradual migration for developers

Example:
```makefile
lint:             ## Lint code with ruff via Nx
	npx nx run-many --target=lint --all

test:             ## Run tests via Nx
	npx nx run-many --target=test --all
```

## Implementation Steps

### Phase 1: Project Configuration (Manual)
1. ✅ Research AWS Nx plugin documentation
2. ✅ Create implementation plan (this document)
3. ⬜ Create `apps/cli/project.json`
4. ⬜ Create `apps/api/project.json`
5. ⬜ Create `libs/core/project.json`
6. ⬜ Update `nx.json` with plugin and targetDefaults
7. ⬜ Verify projects are detected: `npx nx show projects`

### Phase 2: Command Validation (Manual)
8. ⬜ Test `npx nx run cli:lint`
9. ⬜ Test `npx nx run cli:test`
10. ⬜ Test `npx nx run cli:format`
11. ⬜ Test `npx nx run cli:type`
12. ⬜ Test `npx nx run-many --target=lint --all`
13. ⬜ Test `npx nx affected --target=test`

### Phase 3: Integration Updates (Manual)
14. ⬜ Update `package.json` scripts
15. ⬜ Update `.github/workflows/ci.yml`
16. ⬜ Update `Makefile` to use nx internally (backward compat)
17. ⬜ Update `.github/instructions/MAIN.md`
18. ⬜ Update `NX_QUICK_START.md`
19. ⬜ Update `docs/NX_MONOREPO.md`

### Phase 4: Validation (Manual)
20. ⬜ Run full test suite via nx
21. ⬜ Test CI workflow in PR
22. ⬜ Verify caching works (run twice, second should be instant)
23. ⬜ Verify affected detection (change one file, only affected tests run)

## Testing Strategy

### Unit Tests
All existing pytest tests should work without modification:
- Nx executor wraps pytest command
- Test discovery remains the same
- Test markers (`@pytest.mark.unit`) continue to work

### Integration Tests
Test the Nx integration itself:
- Verify projects are detected
- Verify targets execute correctly
- Verify caching behavior
- Verify affected detection

### CI/CD Tests
Validate CI pipeline:
- PR workflow runs affected tests only
- Caching reduces build time
- Parallel execution works
- All quality checks pass

## Acceptance Criteria

- [ ] All Python projects have `project.json` files
- [ ] `npx nx show projects` lists: cli, api, core
- [ ] `npx nx run cli:lint` executes ruff successfully
- [ ] `npx nx run cli:test` executes pytest successfully
- [ ] `npx nx run cli:format` executes black successfully
- [ ] `npx nx run cli:type` executes mypy successfully
- [ ] `npx nx affected --target=test` only tests changed projects
- [ ] CI/CD workflow uses nx commands
- [ ] Agent instructions reference nx commands
- [ ] Documentation updated with nx usage
- [ ] Backward compatibility maintained (Makefile still works)
- [ ] All existing tests pass

## Dependencies

**Required**:
- Node.js 20+ (already required)
- pnpm 10+ (already installed)
- @aws/nx-plugin ^0.65.0 (already installed)
- Python 3.13+ (already required)
- All Python dev dependencies (already installed)

**No new dependencies required** - all tools already present.

## Risk Mitigation

### Risk: Breaking existing workflows
**Mitigation**: Preserve Makefile with backward-compatible targets

### Risk: CI failures during migration
**Mitigation**: Test in feature branch, validate before merging

### Risk: Confusion about command usage
**Mitigation**: Comprehensive documentation updates, keep both approaches documented

### Risk: Performance degradation
**Mitigation**: Nx caching should improve performance; monitor build times

### Risk: Tool configuration issues
**Mitigation**: All tools (ruff, pytest, black, mypy) configured in pyproject.toml, no changes needed

## Future Enhancements

After initial implementation:
1. **Remote Caching**: Configure Nx Cloud for distributed caching
2. **Docker Integration**: Nx executors for Docker-based workflows
3. **Task Dependencies**: Define dependencies between Python projects
4. **Generator Schematics**: Custom Nx generators for new Python modules
5. **Monorepo Expansion**: Add more apps/libs as project grows

## References

- AWS Nx Plugin: https://awslabs.github.io/nx-plugin-for-aws/
- Nx Documentation: https://nx.dev/getting-started/intro
- Repository Structure: docs/NX_MONOREPO.md
- Issue: #319 - Configure Nx for Python
