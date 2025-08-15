# Alpha Releases and Next Branch Workflow

This document describes the alpha release process and how the `next` branch is used for pre-release development.

## Overview

The project uses a dual-branch release strategy:
- **`main` branch**: Stable releases (e.g., `v1.0.0`, `v1.1.0`)
- **`next` branch**: Alpha releases (e.g., `v1.1.0-alpha.1`, `v1.1.0-alpha.2`)

## Alpha Release Process

### 1. Development Workflow

```bash
# Create feature branch from next
git checkout next
git pull origin next
git checkout -b feature/new-alpha-feature

# Make changes and commit using conventional commits
git add .
git commit -m "feat: add new alpha feature"

# Push and create PR targeting next branch
git push origin feature/new-alpha-feature
```

### 2. Pull Request Process

1. Create pull request targeting the `next` branch
2. PR title must follow conventional commit format
3. All CI checks must pass (same as main branch)
4. Code review and approval required
5. Merge to `next` branch

### 3. Automatic Alpha Release

When changes are merged to `next`:

1. **Release-Please Action** automatically:
   - Analyzes conventional commits since last release
   - Creates/updates release PR with alpha version bump
   - Generates changelog with alpha release notes

2. **When Release PR is Merged**:
   - Creates Git tag (e.g., `v1.1.0-alpha.1`)
   - Builds and publishes Docker image with `alpha` tag
   - Uploads Python package to Test PyPI (not production PyPI)
   - Triggers alpha deployment workflow

## Configuration Details

### Release-Please Configuration

The `release-please-config.json` includes branch-specific configuration:

```json
{
  "branches": [
    {
      "branch": "main",
      "packages": { "...": "stable release config" }
    },
    {
      "branch": "next",
      "packages": {
        ".": {
          "prerelease": true,
          "prerelease-type": "alpha",
          "...": "alpha release config"
        }
      }
    }
  ]
}
```

### CI/CD Workflow Updates

All workflows now include the `next` branch:

- **CI Pipeline** (`.github/workflows/ci.yml`): Runs tests on `next` branch
- **Pre-build Validation**: Validates code quality on `next` branch
- **Post-test Actions**: Includes alpha deployment step
- **Pre-commit Workflow**: Full test suite runs on `next` branch

### Docker Image Tagging

Alpha releases use specific Docker tagging strategy:

- **Stable releases**: `latest`, `v1.0.0`, `v1.0`
- **Alpha releases**: `alpha`, `v1.1.0-alpha.1`

### Package Publishing

- **Stable releases**: Published to production PyPI
- **Alpha releases**: Published to Test PyPI for safety

## Version Examples

### Stable Release (main branch)
- Tag: `v1.0.0`
- Docker: `tdorsey/corrupt-video-inspector:v1.0.0`, `tdorsey/corrupt-video-inspector:latest`
- PyPI: `corrupt-video-inspector==1.0.0`

### Alpha Release (next branch)
- Tag: `v1.1.0-alpha.1`
- Docker: `tdorsey/corrupt-video-inspector:v1.1.0-alpha.1`, `tdorsey/corrupt-video-inspector:alpha`
- Test PyPI: `corrupt-video-inspector==1.1.0a1`

## Best Practices

### For Alpha Development

1. **Feature Flags**: Use feature flags for incomplete features
2. **Breaking Changes**: Document breaking changes clearly in alpha releases
3. **Testing**: All alpha releases must pass full test suite
4. **Documentation**: Update docs for alpha features

### Promoting Alpha to Stable

1. **Testing**: Thoroughly test alpha releases
2. **Merge to Main**: Create PR from `next` to `main` for stable release
3. **Version Alignment**: Ensure version consistency between branches
4. **Release Notes**: Combine alpha changelogs for stable release

## Troubleshooting

### Common Issues

1. **Release-Please PR not created**: Check conventional commit format
2. **Alpha version not bumped**: Ensure commits follow semantic versioning
3. **Docker tag not created**: Verify release-please workflow succeeded
4. **Test PyPI upload failed**: Check `TEST_PYPI_API_TOKEN` secret

### Manual Release Creation

If automatic release fails:

```bash
# Create alpha release manually
gh release create v1.1.0-alpha.1 --target next --prerelease --title "v1.1.0-alpha.1" --notes "Alpha release notes"
```

## Monitoring

- **Release Status**: Check GitHub releases page for alpha releases
- **Docker Images**: Verify alpha tags in Docker Hub
- **Test PyPI**: Check package versions in Test PyPI
- **CI Status**: Monitor workflow runs for next branch

## References

- [Release-Please Documentation](https://github.com/googleapis/release-please)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Docker Metadata Action](https://github.com/docker/metadata-action)