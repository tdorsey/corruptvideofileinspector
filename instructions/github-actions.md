# GitHub Actions & CI/CD

## Workflow Patterns, Marketplace Actions, and Automation

### GitHub Actions Overview
- **CI/CD platform**: GitHub Actions for automation
- **Workflows**: Defined in `.github/workflows/`
- **Triggers**: push, pull_request, workflow_dispatch, schedule
- **Best practice**: Prefer marketplace actions over custom code

### Prefer Marketplace Actions

**ALWAYS use well-known marketplace actions before creating custom workflows:**

#### Search Order
1. Search the [GitHub Actions Marketplace](https://github.com/marketplace?type=actions) first
2. Use official GitHub actions when available
3. Use popular community actions with good maintenance
4. Only create custom workflows when marketplace actions don't meet requirements
5. Document the reason for custom solutions in comments

#### Common Recommended Actions
- **Code checkout**: `actions/checkout@v4`
- **Language setup**: `actions/setup-python@v5`, `actions/setup-node@v4`
- **Caching**: `actions/cache@v4`
- **Issue/PR labeling**: `github/issue-labeler@v3.4`
- **File-based labeling**: `actions/labeler@v5`
- **Release automation**: `actions/create-release@v1`
- **Docker**: `docker/build-push-action@v5`

### Custom Workflow Guidelines

When marketplace actions are insufficient:
- Keep custom logic minimal and focused
- Use `actions/github-script@v7` for simple API operations
- **NEVER write Python code to test GitHub Actions workflow files**
- Use `actionlint` or GitHub's built-in validation instead
- Document complex workflows thoroughly
- Consider contributing useful patterns back to the community

### Existing Workflows

#### CI Pipeline (`.github/workflows/ci.yml`)
- Runs on push and pull requests
- Checks code quality (black, ruff, mypy)
- Runs test suite
- Reports coverage
- References make targets:
  - `make check` - Format, lint, type check
  - `make test` - Run all tests
  - `make docker-test` - ✅ Available (placeholder)
  - `make security-scan` - ✅ Available (placeholder)

#### Copilot Setup (`.github/workflows/copilot-setup-steps.yml`)
- Prepares environment for Copilot agents
- Installs system dependencies (FFmpeg, build-essential)
- Installs Python dependencies
- Caches dependencies for performance
- Verifies tools are available

#### Issue Triage (`.github/workflows/issue-triage-agent.yml`)
- Automatically triages new issues
- Classifies issue type
- Applies labels
- Formats according to templates

#### Release Please (`.github/workflows/release-please.yml`)
- Automates release process
- Generates changelogs
- Creates release PRs
- Follows semantic versioning

#### Auto Branch Creation (`.github/workflows/auto-create-branch.yml`)
- Automatically creates branches from issues
- Uses conventional commit format
- Links branch to issue

#### Issue Form Labeler (`.github/workflows/issue-form-labeler.yml`)
- Labels issues based on form fields
- Applies component and type labels
- Maintains consistent labeling

### Workflow Structure

#### Basic Workflow Template
```yaml
name: "Workflow Name"

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  job-name:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run checks
        run: make check
```

### Caching Strategies

#### Pip Caching
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.13'
    cache: 'pip'
```

#### APT Package Caching
```yaml
- name: Cache APT packages
  uses: actions/cache@v4
  with:
    path: /var/cache/apt/archives
    key: ${{ runner.os }}-apt-build-deps-v1
    restore-keys: |
      ${{ runner.os }}-apt-
```

#### Custom Cache
```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cache
      .venv
    key: ${{ runner.os }}-deps-${{ hashFiles('**/poetry.lock') }}
    restore-keys: |
      ${{ runner.os }}-deps-
```

### Secrets and Environment Variables

#### Repository Secrets
- Configure in repository settings
- Access in workflows: `${{ secrets.SECRET_NAME }}`
- Never log secret values
- Use environment-specific secrets

#### Environment Variables
```yaml
env:
  PYTHON_VERSION: '3.13'
  
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DEBUG: 'false'
    steps:
      - run: echo "Python version: $PYTHON_VERSION"
```

### Matrix Testing

#### Multiple Python Versions
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']
    
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
```

#### Multiple Operating Systems
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    
runs-on: ${{ matrix.os }}
```

### Workflow Triggers

#### Push and Pull Request
```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'tests/**'
  pull_request:
    branches: [main]
```

#### Schedule
```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
```

#### Manual Trigger
```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'staging'
```

#### Workflow Call (Reusable)
```yaml
on:
  workflow_call:
    inputs:
      config-path:
        required: true
        type: string
```

### Job Dependencies

#### Sequential Jobs
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: make build
  
  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: make test
  
  deploy:
    needs: [build, test]
    runs-on: ubuntu-latest
    steps:
      - run: make deploy
```

### Artifacts

#### Upload Artifacts
```yaml
- uses: actions/upload-artifact@v4
  with:
    name: test-results
    path: |
      coverage.xml
      htmlcov/
```

#### Download Artifacts
```yaml
- uses: actions/download-artifact@v4
  with:
    name: test-results
    path: ./artifacts
```

### Permissions

#### Minimal Permissions
```yaml
permissions:
  contents: read
  issues: write
  pull-requests: write
```

#### Read-Only Default
```yaml
permissions:
  contents: read
```

### Conditional Execution

#### If Conditions
```yaml
steps:
  - name: Run on main only
    if: github.ref == 'refs/heads/main'
    run: echo "Main branch"
  
  - name: Run on PR
    if: github.event_name == 'pull_request'
    run: echo "Pull request"
```

### Debugging Workflows

#### Enable Debug Logging
Set repository secrets:
- `ACTIONS_RUNNER_DEBUG`: true
- `ACTIONS_STEP_DEBUG`: true

#### Workflow Debugging
```yaml
- name: Debug info
  run: |
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
    echo "Actor: ${{ github.actor }}"
```

### Workflow Best Practices

#### Performance
- Cache dependencies aggressively
- Use appropriate triggers (don't run on every push)
- Fail fast with early validation steps
- Use matrix testing efficiently

#### Security
- Minimize permissions
- Never log secrets
- Use pinned action versions
- Validate external inputs
- Use secrets for sensitive data

#### Maintainability
- Use descriptive names
- Comment complex logic
- Keep workflows focused
- Extract reusable workflows
- Document custom actions

### Workflow Validation

#### Local Validation
```bash
# Install actionlint
brew install actionlint  # macOS
# or download from GitHub releases

# Validate workflow files
actionlint .github/workflows/*.yml
```

#### GitHub UI
- Syntax errors shown when editing
- Workflow runs show detailed logs
- Failed jobs highlight errors

### Copilot Setup Workflow

The `copilot-setup-steps.yml` workflow is critical for agent performance:

#### Current Implementation
- Caches APT packages for faster runs
- Installs FFmpeg and build-essential
- Uses Python setup with pip caching
- Installs dev dependencies
- Verifies tool availability
- Sets up test configuration

#### Optimization Opportunities
- Pre-build container image with dependencies
- Use more aggressive caching
- Parallel dependency installation
- Minimize redundant installations

### Workflow File Commit Instructions

For detailed guidance on workflow file changes, see:
- **[Workflow File Commit Instructions](workflows.md)**

Key points:
- Conventional commit format
- Clear description of workflow purpose
- Test workflows before committing
- Document triggers and dependencies

### Common Patterns

#### Python Project CI
```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: '3.13'
    cache: 'pip'
- run: pip install -e ".[dev]"
- run: make check
- run: make test
```

#### Docker Build
```yaml
- uses: actions/checkout@v4
- uses: docker/setup-buildx-action@v3
- uses: docker/build-push-action@v5
  with:
    context: .
    push: false
    tags: app:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Troubleshooting

#### Common Issues
- **Workflow not triggered**: Check trigger conditions
- **Permission errors**: Review job permissions
- **Cache not working**: Verify cache key
- **Timeout**: Increase timeout or optimize steps
- **Secret not available**: Check secret configuration

#### Viewing Logs
```bash
# Using gh CLI
gh run list
gh run view <run-id>
gh run view <run-id> --log
```

### CI/CD Best Practices Summary
- **Use marketplace actions** whenever possible
- **Cache dependencies** aggressively
- **Minimize permissions** to least privilege
- **Validate workflows** before committing
- **Document custom logic** thoroughly
- **Keep workflows focused** on single responsibility
- **Use matrix testing** for multiple configurations
- **Fail fast** with early validation
- **Monitor workflow performance** and optimize
- **Review workflow logs** to identify issues
