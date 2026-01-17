---
applyTo: ".github/workflows/*.yml"
---

# GitHub Actions Workflow Instructions

When creating or modifying GitHub Actions workflow files, follow these guidelines:

## Workflow Standards

### Prefer Marketplace Actions
**ALWAYS** use well-known marketplace actions before creating custom workflows:
- Search the [GitHub Actions Marketplace](https://github.com/marketplace?type=actions) first
- Use official GitHub actions (e.g., `actions/checkout`, `actions/setup-python`) when available
- Use popular community actions with good maintenance and star ratings
- Only create custom workflows when marketplace actions don't meet specific requirements

### Common Recommended Actions
```yaml
- name: Checkout code
  uses: actions/checkout@v4

- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.13'

- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
```

## Required Workflow Components

### 1. Proper Job Names and Descriptions
```yaml
name: Lint, Format, and Type Check

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality-check:
    name: Code Quality Checks
    runs-on: ubuntu-latest
```

### 2. Dependency Caching
Always cache dependencies to speed up workflows:
```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### 3. Timeout Configuration
Set reasonable timeouts to prevent hung jobs:
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30  # Prevent infinite runs
```

### 4. Permission Scoping
Use minimal required permissions:
```yaml
permissions:
  contents: read
  pull-requests: write  # Only if needed
```

## This Repository's Workflow Patterns

### Quality Checks Workflow
```yaml
# .github/workflows/quality.yml
- name: Install dependencies
  run: |
    pip install --upgrade pip
    pip install -e ".[dev]"

- name: Run quality checks
  run: make check  # Runs black, ruff, mypy
```

### Test Workflow
```yaml
# .github/workflows/test.yml
- name: Install FFmpeg
  run: sudo apt-get install -y ffmpeg

- name: Run tests
  run: make test
  
- name: Upload coverage
  uses: codecov/codecov-action@v3
  if: always()
```

### Docker Build Workflow
```yaml
# .github/workflows/docker.yml
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: false
    tags: corruptvideofileinspector:test
```

## Security Best Practices

### 1. No Hardcoded Secrets
```yaml
# ❌ NEVER hardcode secrets
env:
  API_KEY: "abc123"

# ✅ Use GitHub Secrets
env:
  API_KEY: ${{ secrets.API_KEY }}
```

### 2. Pin Action Versions
```yaml
# ❌ Risky - uses latest
- uses: actions/checkout@main

# ✅ Safe - pinned version
- uses: actions/checkout@v4
```

### 3. Restrict Workflow Triggers
```yaml
# Limit what can trigger workflows
on:
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:  # Manual trigger only
```

## Validation

### Test Workflow Syntax
Use actionlint or GitHub's validation:
```bash
# Install actionlint
brew install actionlint  # macOS
# or
go install github.com/rhysd/actionlint/cmd/actionlint@latest

# Validate workflow files
actionlint .github/workflows/*.yml
```

### Never Write Python to Test Workflows
- ❌ Don't write Python scripts to test workflow files
- ✅ Use actionlint or GitHub's built-in validation
- ✅ Test workflows with actual PR triggers

## Common Workflow Jobs for This Repo

### 1. PR Title Validation
```yaml
- name: Validate PR Title
  uses: amannn/action-semantic-pull-request@v5
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Code Quality
```yaml
- name: Run make check
  run: make check
  timeout-minutes: 10
```

### 3. Tests
```yaml
- name: Run tests
  run: make test
  timeout-minutes: 30
```

### 4. Docker Build
```yaml
- name: Build Docker image
  run: make docker-build
  timeout-minutes: 20
```

### 5. Security Scan
```yaml
- name: Run security scan
  run: make security-scan
  timeout-minutes: 10
```

## Workflow File Commit Guidelines

When committing workflow changes:
```bash
# Commit message format
chore(ci): <description>

# Examples
chore(ci): add caching for pip dependencies
chore(ci): update Python version to 3.13
chore(ci): add security scanning workflow
```

## Common Mistakes to Avoid

❌ Not using marketplace actions
❌ Missing timeout configuration
❌ Hardcoding secrets
❌ Using unpinned action versions
❌ No dependency caching
❌ Overly broad permissions
❌ Complex custom bash scripts (use actions instead)
❌ Not testing workflow syntax before commit

## Debugging Workflows

```yaml
# Add debug steps
- name: Debug environment
  run: |
    echo "Runner OS: ${{ runner.os }}"
    echo "Python version: $(python --version)"
    echo "Working directory: $(pwd)"
    ls -la
```

## Documentation

Always update workflow documentation when:
- Adding new workflows
- Changing workflow behavior
- Adding required secrets
- Modifying triggers or permissions
