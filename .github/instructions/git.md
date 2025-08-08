# ---
applyTo: "**"
# ---
# Git and Version Control Instructions

## Commit Message Guidelines

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages. Please ensure your commit messages adhere to the following format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc.)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries such as documentation generation

### Examples
- `feat(auth): add login functionality`
- `fix(video): resolve playback issue`
- `docs(readme): update installation instructions`
- `test(utils): add unit tests for file processing`
- `chore(deps): update dependencies to latest versions`

### Why Conventional Commits?
Using Conventional Commits helps:
- Automate the release process
- Generate changelogs automatically
- Determine semantic version bumps
- Communicate the nature of changes clearly
- Trigger build and publish processes

## Branch Management

### Branch Naming
- Use descriptive branch names that indicate the purpose
- Follow patterns like:
  - `feature/feature-name`
  - `fix/bug-description`
  - `docs/documentation-update`
  - `refactor/component-name`

### Pull Request Guidelines
- Keep pull requests focused on a single feature or fix
- Include descriptive titles and detailed descriptions
- Reference related issues when applicable
- Ensure all checks pass before requesting review

## Pre-commit Considerations

### Code Quality Checks
- Ensure code formatting is applied before committing
- Run linting tools to catch style issues
- Verify type checking passes if using mypy
- Run tests to ensure functionality isn't broken


## Linting and Formatting
- **Prefer running formatting tools (e.g., black, ruff) and allowing them to auto-fix lint errors, rather than manually rewriting or sorting entire files.**
- Automated tools ensure consistency and reduce the risk of introducing errors during manual changes.

## Pull Request Requirements

### Quality Standards (Critical)
- **Pull requests MUST NOT have conflicts, test failures, or lint errors**
- **Run `make check` before every commit** to ensure code quality
- **All tests must pass** before submitting changes
- **Follow existing code style and patterns** in the repository

### Development Workflow for Pull Requests
1. **Make minimal, focused changes** that address the specific issue
2. **Format code**: `make format` to fix Black and Ruff issues
3. **Run full checks**: `make check` to validate quality standards
4. **Test changes**: `make test` to ensure functionality
5. **Commit only when all checks pass** - no exceptions

### Documentation Updates
- Update relevant documentation when making changes
- Ensure README and other docs reflect current functionality
- Update environment variable documentation when needed
