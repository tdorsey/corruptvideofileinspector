# ---
applyTo: ".github/workflows/*.yml"
# ---
# GitHub Actions and CI/CD Instructions

This project uses GitHub Actions for continuous integration, automated testing, and release management. Understanding the workflow structure and CI/CD patterns is essential for maintaining and extending the automation.

## Workflow Files Overview

The project contains multiple workflow files in `.github/workflows/`:

### 1. ci.yml - Continuous Integration
**Purpose**: Runs on every push and pull request to validate code quality and run tests
**Key Components**:
- Lint and format validation using `make lint` and `make format`
- Test execution with `make test` (runs both unit and integration tests)
- Python 3.13 setup with pip caching
- Parallel job execution for faster feedback

### 2. workflow-validation.yml - GitHub Actions Validation
**Purpose**: Validates syntax of GitHub Actions workflow files on PR changes
**Key Components**:
- Triggers on PRs that modify `.github/workflows/*.yml` or `.github/workflows/*.yaml`
- Uses `actionlint` via `devops-actions/actionlint@v0.1.9` for comprehensive validation
- Required check that blocks merging if workflow syntax errors are found
- Reports validation results for changed workflow files

### 3. release.yml - Release Automation
**Purpose**: Handles version bumping, Docker builds, and PyPI publishing
**Key Components**:
- Automated version incrementation using conventional commits
- Multi-platform Docker builds (linux/amd64, linux/arm64)
- PyPI package publishing with proper authentication
- GitHub release creation with automated changelog generation
- Docker image publishing to GitHub Container Registry

### 4. copilot-setup-steps.yml - Copilot Environment
**Purpose**: Prepares the development environment for GitHub Copilot agents
**Key Components**:
- Python 3.13 environment setup
- Development dependency installation via `make install-dev`
- Pre-commit hook preparation (commented sections for optional setup)

## CI/CD Architecture Patterns

### Trigger Patterns
```yaml
# Standard CI triggers
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

# Path-based triggers for specific workflows
on:
  push:
    paths:
      - .github/workflows/copilot-setup-steps.yml

# Manual workflow dispatch
on:
  workflow_dispatch:
```

### Job Structure
```yaml
jobs:
  lint-and-format:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: 'pip'

      - name: Install dependencies
        run: make install-dev

      - name: Run linting
        run: make lint

      - name: Check formatting
        run: make format
```

## Make Command Integration

The CI workflows heavily rely on Makefile targets for consistency:

- `make install-dev`: Install development dependencies including pre-commit hooks
- `make lint`: Run ruff linting checks
- `make format`: Run black formatting validation
- `make test`: Execute pytest with unit and integration tests
- `make docker-build`: Build Docker images for testing
- `make pre-commit-run`: Run all pre-commit hooks

## Release Workflow Details

### Version Management
- Uses conventional commit messages for automatic version bumping
- Supports semantic versioning (major.minor.patch)
- Automatically generates changelogs from commit history

### Docker Multi-Platform Builds
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push Docker image
  uses: docker/build-push-action@v6
  with:
    platforms: linux/amd64,linux/arm64
    push: true
    tags: |
      ghcr.io/${{ github.repository }}:latest
      ghcr.io/${{ github.repository }}:${{ steps.version.outputs.new_version }}
```

### PyPI Publishing
- Uses trusted publishing with OpenID Connect (no API tokens required)
- Builds both source distribution (sdist) and wheel packages
- Publishes to PyPI only on successful builds and tests

## Secrets and Environment Variables

### Required Repository Secrets
- `PYPI_API_TOKEN`: For PyPI package publishing (if not using trusted publishing)
- `GITHUB_TOKEN`: Automatically provided for GitHub API access

### Trakt Integration (Optional)
- `TRAKT_CLIENT_ID`: Stored in `docker/secrets/trakt_client_id.txt`
- `TRAKT_CLIENT_SECRET`: Stored in `docker/secrets/trakt_client_secret.txt`

## Working with Workflows

### Local Testing
Before pushing workflow changes:
```bash
# Validate workflow syntax with actionlint (recommended)
curl -sSL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash | bash -s -- latest /tmp
/tmp/actionlint .github/workflows/*.yml

# Standard project validation
make lint

# Test the commands that workflows will run
make install-dev
make lint
make format
make test
```

### Debugging Failed Workflows
1. Check the Actions tab in GitHub repository
2. Review failed job logs
3. Look for common issues:
   - Missing dependencies
   - Test failures
   - Linting violations
   - Docker build errors

### Workflow Permissions
Each workflow uses minimal required permissions:
```yaml
permissions:
  contents: read        # Read repository contents
  packages: write       # Push Docker images
  id-token: write       # PyPI trusted publishing
```

## Adding New Workflows

### Basic Workflow Template
```yaml
name: "New Workflow"

on:
  push:
    branches: [ main ]

jobs:
  job-name:
    runs-on: ubuntu-latest
    permissions:
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"
          cache: 'pip'

      - name: Install dependencies
        run: make install-dev

      - name: Run custom task
        run: echo "Add your commands here"
```

### Best Practices
1. **Use specific action versions** (e.g., `@v4`, not `@main`)
2. **Cache dependencies** when possible to speed up builds
3. **Use matrix builds** for testing multiple Python versions if needed
4. **Set appropriate permissions** (principle of least privilege)
5. **Use environment variables** for configuration
6. **Add meaningful step names** for better debugging

## Monitoring and Maintenance

### Regular Maintenance Tasks
- Update action versions quarterly
- Review and update Python version compatibility
- Monitor workflow run times and optimize if needed
- Keep dependencies in sync between local dev and CI

### Performance Optimization
- Use caching for pip dependencies
- Parallel job execution where possible
- Minimize Docker layer rebuilds
- Use appropriate runner types (ubuntu-latest for most cases)

## Integration with Development Tools

The workflows integrate with the project's development toolchain:
- **Pre-commit hooks**: Workflows mirror pre-commit hook checks
- **Docker**: CI validates Docker builds work correctly
- **pytest**: Both unit and integration tests run in CI
- **Code quality**: Linting and formatting enforced consistently

This ensures that CI/CD processes match the local development experience and catch issues early in the development cycle.
