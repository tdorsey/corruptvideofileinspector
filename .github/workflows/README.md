# CI/CD Workflows

This directory contains GitHub Actions workflows for automated testing, building, and deployment.

## Workflows

### ci.yml - Continuous Integration
Runs on every push and pull request to main/develop branches:

- **Lint, Format, and Type Check**: Uses black, ruff, and mypy to ensure code quality
- **Test**: Runs pytest with basic import and functionality tests
- **Docker**: Builds and tests the Docker image
- **Security**: Runs Trivy security scanning

### pr-title-check.yml - Pull Request Validation
Runs on pull request events (opened, edited, synchronize):

- **Semantic PR Title Validation**: Uses `amannn/action-semantic-pull-request@v5` to ensure PR titles follow conventional commit format
- **Issue Reference Validation**: Checks that PRs reference an issue number in title or body
- **Automated Draft Conversion**: Sets PRs to draft status when validation fails
- **User Feedback**: Posts detailed comments explaining validation failures and how to fix them
- **Assignee Notifications**: Notifies PR assignees when validation fails

**Supported PR Title Formats:**
- `feat: add new feature (#123)`
- `fix: resolve video corruption issue`
- `docs: update API documentation`
- `chore: update dependencies (#456)`

**Required Issue References:**
- In title: `feat: add feature (#123)`
- In body: `Fixes #123`, `Closes #456`, or similar

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
- PR title validation to pass
- Up-to-date branches before merging
- At least one review for pull requests

### Workflow Permissions
Each workflow uses minimal required permissions:
- **ci.yml**: `contents: read` for repository access
- **pr-title-check.yml**: `contents: read`, `pull-requests: write`, `issues: read` for PR management
- **release.yml**: `contents: write`, `packages: write`, `id-token: write` for publishing

## Development

The CI workflow ensures that all code changes:
1. Follow consistent formatting (black)
2. Pass linting checks (ruff)
3. Pass type checking (mypy)
4. Have working imports and basic functionality
5. Build successfully in Docker
6. Pass security scans

This helps maintain code quality and prevents broken builds from being merged.