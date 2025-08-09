# Repository Configuration and Code Ownership

This document describes how repository settings and code ownership are managed in the Corrupt Video Inspector project.

## Repository Settings Management

### Overview

Repository settings are managed declaratively through the `.github/settings.yaml` file. This approach provides:

- **Version Control**: All repository configuration changes are tracked in git history
- **Consistency**: Settings are documented and reproducible across environments
- **Security**: Changes require code review through the pull request process
- **Transparency**: Anyone can see the current and historical repository configuration

### Settings File Structure

The `.github/settings.yaml` file contains the following sections:

#### Repository Properties
- Basic repository information (name, description, topics)
- Feature toggles (issues, projects, wiki, etc.)
- Merge and branch settings
- Security and vulnerability settings

#### Branch Protection Rules
- **Main Branch**: Strict protection with required status checks and code owner reviews
- **Develop Branch**: Relaxed protection for development workflow
- Status check requirements aligned with CI/CD pipeline

#### Labels
Comprehensive label system for issue and PR management:
- **Type Labels**: `type: bug`, `type: feature`, `type: enhancement`, etc.
- **Priority Labels**: `priority: critical` through `priority: low`
- **Status Labels**: `status: blocked`, `status: in-progress`, etc.
- **Component Labels**: `component: cli`, `component: core`, etc.
- **Special Labels**: `good first issue`, `help wanted`, `security`, etc.

#### Security Settings
- Secret scanning and push protection
- Dependency graph and Dependabot integration
- Automated security fix notifications

### Modifying Repository Settings

1. **Create a Pull Request**: Never modify `.github/settings.yaml` directly on main branch
2. **Code Owner Review**: Changes require approval from repository maintainers (defined in CODEOWNERS)
3. **Testing**: Validate settings in a test environment if possible
4. **Documentation**: Update this documentation if adding new setting categories

### Settings Deployment

**Note**: The `.github/settings.yaml` file serves as documentation and a source of truth. Actual application of these settings to the repository requires:

1. **GitHub Apps**: Install a repository settings management app like [Probot Settings](https://github.com/probot/settings)
2. **GitHub API**: Use scripts or tools that apply settings via GitHub's REST API
3. **Manual Application**: Apply settings through GitHub's web interface using the file as a reference

## Code Ownership (CODEOWNERS)

### Overview

The `CODEOWNERS` file defines who owns different parts of the codebase. Code owners are automatically requested for review when someone opens a pull request that modifies code they own.

### Ownership Structure

#### Global Ownership
- **@tdorsey**: Repository owner with final authority on all changes

#### Critical Configuration Files
Files that control repository behavior and security:
- `.github/settings.yaml` - Repository settings (this file)
- `.github/workflows/` - CI/CD pipeline definitions  
- `CODEOWNERS` - Code ownership definitions
- `pyproject.toml` and `poetry.lock` - Dependency management
- Docker and deployment configurations

#### Application Domains
- **CLI Module** (`/src/cli/`): Command-line interface components
- **Core Module** (`/src/core/`): Business logic and core functionality
- **FFmpeg Integration** (`/src/ffmpeg/`): Video processing logic
- **Configuration** (`/src/config/`): Configuration management

#### Documentation and Testing
- Documentation files require maintainer review for consistency
- Test files require review to ensure quality and coverage

### Adding New Code Owners

1. **Identify Domain Expertise**: New owners should have demonstrated expertise in specific areas
2. **Update CODEOWNERS**: Add entries following the existing pattern
3. **Get Approval**: CODEOWNERS changes require approval from existing owners
4. **Communicate**: Notify the team about ownership changes

### Code Owner Responsibilities

- **Timely Reviews**: Respond to review requests promptly
- **Quality Gate**: Ensure changes meet project standards
- **Knowledge Transfer**: Help onboard other contributors
- **Domain Maintenance**: Keep owned areas well-documented and tested

## Best Practices

### For Maintainers

1. **Review Thoroughly**: Pay special attention to changes in owned areas
2. **Document Changes**: Significant configuration changes should be documented
3. **Test Impact**: Consider the broader impact of repository setting changes
4. **Communicate**: Discuss major changes with the team before implementation

### For Contributors

1. **Check Ownership**: Review CODEOWNERS before making changes
2. **Engage Early**: Discuss significant changes with code owners before implementation
3. **Follow Process**: Always use pull requests for protected files
4. **Be Patient**: Code owner reviews may take time due to their critical nature

### Security Considerations

1. **Protected Files**: Never bypass code owner reviews for protected files
2. **Access Control**: Repository settings control who can do what - changes affect security
3. **Audit Trail**: All changes to protected files should have clear justification
4. **Principle of Least Privilege**: Only grant necessary permissions

## Troubleshooting

### Common Issues

1. **Settings Not Applied**: Remember that `.github/settings.yaml` requires tooling to apply
2. **Review Requirements**: Protected file changes always require code owner approval
3. **Merge Conflicts**: Coordinate with other maintainers when multiple people edit protected files
4. **Permission Errors**: Check that you have necessary repository permissions

### Getting Help

- Open an issue for questions about repository configuration
- Tag @tdorsey for urgent configuration or ownership questions
- Check GitHub's documentation for CODEOWNERS and repository settings

## References

- [GitHub CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [GitHub Repository Settings API](https://docs.github.com/en/rest/repos/repos)
- [Probot Settings App](https://github.com/probot/settings)
- [Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/managing-a-branch-protection-rule)