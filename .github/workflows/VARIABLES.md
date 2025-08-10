# Repository Variables

This document describes the repository variables used across GitHub Actions workflows in this project.

## Overview

Repository variables are used to centrally manage action versions across all workflows. This ensures consistency and makes it easier to update action versions when needed.

## Required Variables

The following repository variables must be configured in the repository settings:

### Core GitHub Actions

| Variable | Description | Current Recommended Value |
|----------|-------------|---------------------------|
| `ACTIONS_VERSIONS_CHECKOUT` | actions/checkout version | `v4` |
| `ACTIONS_VERSIONS_SETUP_PYTHON` | actions/setup-python version | `v5` |
| `ACTIONS_VERSIONS_GITHUB_SCRIPT` | actions/github-script version | `v7` |

### Docker Actions

| Variable | Description | Current Recommended Value |
|----------|-------------|---------------------------|
| `ACTIONS_VERSIONS_SETUP_BUILDX` | docker/setup-buildx-action version | `v3` |
| `ACTIONS_VERSIONS_LOGIN_ACTION` | docker/login-action version | `v3` |
| `ACTIONS_VERSIONS_METADATA_ACTION` | docker/metadata-action version | `v5` |
| `ACTIONS_VERSIONS_BUILD_PUSH_ACTION` | docker/build-push-action version | `v5` |

### Artifact and Release Actions

| Variable | Description | Current Recommended Value |
|----------|-------------|---------------------------|
| `ACTIONS_VERSIONS_UPLOAD_ARTIFACT` | actions/upload-artifact version | `v4` |
| `ACTIONS_VERSIONS_DOWNLOAD_ARTIFACT` | actions/download-artifact version | `v4` |
| `ACTIONS_VERSIONS_GH_RELEASE` | softprops/action-gh-release version | `v2` |

### Additional Actions

| Variable | Description | Current Recommended Value |
|----------|-------------|---------------------------|
| `ACTIONS_VERSIONS_SEMANTIC_PULL_REQUEST` | amannn/action-semantic-pull-request version | `v5` |
| `ACTIONS_VERSIONS_AUTO_ASSIGN_ISSUE` | pozil/auto-assign-issue version | `v2.2.0` |
| `ACTIONS_VERSIONS_ISSUE_LABELER` | github/issue-labeler version | `v3.4` |

### Build Configuration

| Variable | Description | Current Recommended Value |
|----------|-------------|---------------------------|
| `ACTIONS_DOCKER_BUILD_PLATFORMS` | Docker build platforms | `linux/amd64,linux/arm64` |
| `PYTHON_VERSION` | Python version for builds | `3.13` |

## How to Configure

1. Go to **Repository Settings** → **Secrets and variables** → **Actions** → **Variables tab**
2. Add each variable listed above with its recommended value
3. Ensure all variable names match exactly (case-sensitive)

## Validation

The repository includes an automated validation workflow that checks if all required variables are properly configured:

- **Workflow**: `.github/workflows/internal/validate-repository-variables.yml`
- **Trigger**: Called by other workflows or can be run manually
- **Output**: Validation report showing missing or misconfigured variables

## Usage in Workflows

Variables are referenced in workflow files using the `vars` context:

```yaml
- name: Checkout code
  uses: actions/checkout@${{ vars.ACTIONS_VERSIONS_CHECKOUT }}
```

## Maintenance

- Review and update variable values when new action versions are released
- Use the validation workflow to ensure all workflows remain compatible
- Test workflows after updating action versions

## Benefits

- **Consistency**: All workflows use the same action versions
- **Maintainability**: Update versions in one place rather than across multiple files
- **Security**: Centralized control over action versions used in the repository
- **Auditability**: Clear tracking of which action versions are approved for use
