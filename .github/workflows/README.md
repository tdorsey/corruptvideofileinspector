# GitHub Workflows Architecture

This directory contains the restructured GitHub Actions workflows using an action-oriented and event-oriented architecture.

## Structure Overview

```
.github/workflows/
├── actions/           # Action-oriented (reusable) workflows
│   ├── build.yml      # Build Python packages and Docker images
│   ├── test.yml       # Run Python and Docker tests
│   ├── python-quality.yml  # Code quality checks (lint, format, type)
│   ├── security-scan.yml   # Security scanning
│   └── release-build.yml   # Release-specific build tasks
├── events/            # Event-oriented (caller) workflows
│   ├── build-test.yml # Main CI pipeline (renamed from build-test.yml)
│   ├── pre-commit.yml # Pre-commit validation
│   └── post-test.yml  # Post-test actions and cleanup
├── ci/               # Legacy CI workflows (transitioning)
│   ├── ci.yml        # Updated to use action-oriented workflows
│   └── pr-title-check.yml  # PR title validation
├── internal/         # Internal utility workflows
└── repository/       # Repository management workflows
```

## Action-Oriented Workflows (Reusable)

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

### `actions/test.yml`
- **Purpose**: Execute project tests (unit, integration, or all) optionally using a pre-built Docker image
- **Inputs**: python-version, test-type (unit|integration|all), coverage (true|false), docker-image (optional)
- **Outputs**: coverage-artifact (when coverage=true), test-results
- **Used by**: CI pipeline, pre-commit validation
- **Note**: Build/publish tasks are handled by `actions/build.yml`; release packaging by `actions/release-build.yml`

### `actions/python-quality.yml`
- **Purpose**: Code quality checks (formatting, linting, type checking)
- **Inputs**: python-version, check-format, run-lint, run-type-check
- **Used by**: CI pipeline, pre-commit validation

### `actions/security-scan.yml`
- **Purpose**: Security scanning for dependencies, code, and Docker images
- **Inputs**: scan-dependencies, scan-code, scan-docker, docker-image
- **Used by**: CI pipeline, release workflows

### `actions/release-build.yml`
- **Purpose**: Release-specific build and deployment tasks
- **Inputs**: python-version, push-to-registry
- **Used by**: Release workflows
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password/token

<<<<<<< HEAD
## Event-Oriented Workflows (Callers)

### `events/build-test.yml` (Main CI Pipeline)
- **Triggers**: Push to main/develop, PRs to main
- **Jobs**:
  1. Build (calls `actions/build.yml`)
  2. Test (calls `actions/test.yml`)
  3. Security scan (calls `actions/security-scan.yml`)
  4. CI summary
- **Purpose**: Main CI/CD pipeline for validating code changes

### `events/pre-commit.yml`
- **Triggers**: PR opened/synchronized, pushes to feature branches
- **Jobs**:
  1. Quality checks (calls `actions/python-quality.yml`)
  2. Quick unit tests (calls `actions/test.yml`)
  3. Pre-commit summary
- **Purpose**: Fast feedback for developers before full CI

### `events/post-test.yml`
- **Triggers**: CI Pipeline completion
- **Jobs**:
  1. Deploy to staging (develop branch)
  2. Prepare release (main branch)
  3. Update documentation
  4. Cleanup old artifacts
  5. Notifications
- **Purpose**: Actions to take after successful CI completion

## Benefits of This Architecture

### 1. **Separation of Concerns**
- **Actions**: Focus on specific tasks (build, test, lint)
- **Events**: Focus on when and how to orchestrate actions

### 2. **Reusability**
- Action workflows can be called from multiple event workflows
- Consistent behavior across different scenarios
- Easy to test and maintain individual actions

### 3. **Flexibility**
- Event workflows can mix and match actions as needed
- Easy to add new event triggers without duplicating action logic
- Different event workflows can use different parameters for the same action

### 4. **Maintainability**
- Changes to build/test logic only need to be made in one place
- Clear separation between "what to do" (actions) and "when to do it" (events)
- Easier debugging and troubleshooting

### 5. **Performance**
- Pre-commit validation runs only necessary checks for fast feedback
- Full CI pipeline runs comprehensive validation
- Post-test actions don't block the main pipeline

## Usage Examples

### Running Quality Checks Only
```yaml
quality:
  uses: ./.github/workflows/actions/python-quality.yml
  with:
    python-version: '3.13'
    check-format: true
    run-lint: true
    run-type-check: false
```

### Running Tests with Coverage
```yaml
test:
  uses: ./.github/workflows/actions/test.yml
  with:
    python-version: '3.13'
    test-type: 'all'
    coverage: true
    docker-image: 'my-app:latest'
```

### Building for Release
```yaml
build:
  uses: ./.github/workflows/actions/build.yml
  with:
    python-version: '3.13'
    platforms: 'linux/amd64,linux/arm64'
    push: true
    tags: 'my-app:v1.0.0,my-app:latest'
```

## Legacy Workflows

### `ci/pr-title-check.yml` - Pull Request Validation
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

## Migration Notes

- **Old workflows**: `docker-build.yml` and `python-test.yml` have been consolidated into `build.yml` and `test.yml`
- **CI workflow**: Updated to use action-oriented workflows
- **New event workflows**: Added for better event handling and post-processing
- **Backward compatibility**: Existing functionality is preserved with improved structure

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
