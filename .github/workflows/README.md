# CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing, building, and deployment.

## Workflows

### ci.yml - Continuous Integration
Runs on every push and pull request to main/develop branches:

- **Lint, Format, and Type Check**: Uses black, ruff, and mypy to ensure code quality
- **Test**: Runs pytest with basic import and functionality tests
- **Docker**: Builds and tests the Docker image
- **Security**: Runs Trivy security scanning

### release.yml - Release Automation
Runs when version tags are pushed:

- **Build**: Creates Python package builds
- **Docker**: Builds and pushes multi-platform Docker images to Docker Hub
- **GitHub Release**: Creates GitHub releases automatically
- **PyPI**: Publishes packages to PyPI (when configured)

## Setup

### Required Secrets
For the release workflow to work fully, add these secrets to your repository:

- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password/token
- `PYPI_API_TOKEN`: PyPI API token for package publishing

### Branch Protection
Consider setting up branch protection rules for the main branch that require:
- CI checks to pass
- Up-to-date branches before merging
- At least one review for pull requests

## Development

The CI workflow ensures that all code changes:
1. Follow consistent formatting (black)
2. Pass linting checks (ruff)
3. Pass type checking (mypy)
4. Have working imports and basic functionality
5. Build successfully in Docker
6. Pass security scans

This helps maintain code quality and prevents broken builds from being merged.