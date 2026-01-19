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
- **build**: Changes that affect the build system or external dependencies (pip, poetry, npm, etc.)
- **chore**: Changes to the build process or auxiliary tools and libraries such as documentation generation

### Agent and Skill Changes are Documentation

**IMPORTANT: Custom agent and skill changes are contributor documentation, NOT user-facing features.**

Changes to GitHub Copilot agents and skills should use the `docs` type because they are development tools that help contributors work more effectively. They document how to contribute to the project, not add features to the application itself.

**What qualifies as agent/skill documentation:**
- Files in `.github/agents/` directory → use `docs(agents):`
- Files in `.github/skills/` directory → use `docs(skills):`
- Agent-related Copilot instructions → use `docs(copilot):` or `docs(agents):`
- Workflow files that support agent functionality → use `docs(agents):` or `ci(agents):`

**Examples:**

✅ **Correct:**
```bash
docs(agents): add issue creation agent
docs(agents): update lint-error agent with improved error detection
docs(skills): create issue creation skill
docs(copilot): update agent usage guidelines in instructions
```

❌ **Incorrect:**
```bash
feat(agents): add issue creation agent      # Wrong - agents aren't user features
feat: create lint-error agent               # Wrong - this is contributor documentation
chore(agents): update issue creation agent  # Wrong - use docs, not chore
```

### Description Format Rules
- **Description must start with lowercase letter** (after the type and scope)
- **Description must NOT end with punctuation** (no period, exclamation mark, etc.)
- **Only use valid commit types** from the list above

### Examples

#### ✅ Passing Commits
- `feat(auth): add login functionality`
- `fix(video): resolve playback issue`
- `docs(readme): update installation instructions`
- `test(utils): add unit tests for file processing`
- `build(deps): update python dependencies to latest versions`

#### ❌ Failing Commits
- `feat(auth): Add login functionality` (description starts with capital letter)
- `fix(video): resolve playback issue.` (description ends with punctuation)
- `feature(auth): add login functionality` (invalid type - should be `feat`)
- `fix(video): Resolve playback issue!` (capital letter AND punctuation)
- `chore(deps): update dependencies` (invalid type - should be `build` for dependencies)

### Breaking Changes
For commits that introduce breaking changes, use the `!` suffix after the type/scope and include `BREAKING CHANGE:` in the footer:

#### Format for Breaking Changes
```
<type>[optional scope]!: <description>

[optional body]

BREAKING CHANGE: <description of the breaking change>
```

#### Examples of Breaking Change Commits
- `feat(api)!: remove deprecated endpoint`
- `refactor(config)!: change configuration file format`
- `fix(auth)!: update authentication method`

#### Full Breaking Change Example
```
feat(trakt)!: change default sync behavior from corrupt to healthy files

BREAKING CHANGE: The default `include_statuses` for Trakt sync operations
has changed from `[CORRUPT, SUSPICIOUS]` to `[HEALTHY]`. Users who want
the previous behavior must explicitly configure the old statuses.
```

### Atomic Commits (REQUIRED)
- **Each commit should represent a single, focused change**
- **Avoid combining unrelated changes in one commit**
- Examples of good atomic commits:
  - One commit for adding a feature
  - Separate commit for updating documentation related to that feature
  - Separate commit for adding tests for that feature
- Examples of bad commits (combining unrelated changes):
  - Fixing a bug + adding a new feature + updating documentation in one commit
  - Changing multiple unrelated files or components in one commit

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
- **Include issue number in branch names** for traceability
- Follow patterns like:
  - `feature/123-feature-name` (for issue #123)
  - `fix/456-bug-description` (for issue #456)
  - `docs/789-documentation-update` (for issue #789)
  - `refactor/101-component-name` (for issue #101)

### Pull Request Guidelines
- Keep pull requests focused on a single feature or fix
- **PR titles MUST follow Conventional Commits format** (same as commit messages)
- **PR titles must start with lowercase** after the type/scope
- Include descriptive titles and detailed descriptions
- **Reference related issues in PR description** using `#issue-number` (e.g., "Fixes #123" or "Addresses #456")
- Ensure all checks pass before requesting review

#### PR Title Format (REQUIRED)
PR titles must follow the same Conventional Commits format:
```
<type>[optional scope]: <description>
```

**Examples of valid PR titles:**
- `feat(auth): add OAuth2 authentication`
- `fix(video): resolve memory leak in scanner`
- `docs(readme): update installation guide`
- `refactor(database): optimize query performance`
- `test(api): add integration tests for endpoints`

**Examples of INVALID PR titles:**
- `Consolidate issue automation workflows` ❌ (missing type)
- `Fix: Update database` ❌ (description starts with capital)
- `feat(auth): Add OAuth2.` ❌ (capital letter and period)

**CI Check:** The `Validate PR Title` job will fail if the PR title doesn't follow this format.

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

### Merge Conflict Resolution (REQUIRED)
**Before submitting or updating a pull request:**
- **MUST resolve all merge conflicts** - PRs with unresolved conflicts will be rejected
- Check for conflicts: `git status` and look for "both modified" files
- Resolve conflicts manually or with merge tools: `git mergetool`
- After resolving, stage changes: `git add <resolved-files>`
- Complete the merge: `git commit` (or `git merge --continue` / `git rebase --continue`)
- Verify resolution: `git diff origin/main` to review all changes
- The pre-commit hook `check-merge-conflict` will automatically detect any remaining conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)

### Dependency Management (REQUIRED)
**When dependencies are added or modified:**
- **MUST update `poetry.lock`** after changing dependencies in `pyproject.toml`
- Update lock file: `poetry lock --no-update` (for specific changes) or `poetry lock` (for full update)
- Validate consistency: `poetry check` to ensure pyproject.toml and poetry.lock are in sync
- **MUST commit `poetry.lock`** alongside `pyproject.toml` changes
- Document dependency changes in commit message and PR description

### Development Workflow for Pull Requests
1. **Sync with main branch**: `git fetch origin && git merge origin/main` (or rebase)
2. **Resolve any merge conflicts** following the process above
3. **Make minimal, focused changes** that address the specific issue
4. **Update dependencies if needed** and run `poetry lock` if `pyproject.toml` changed
5. **Format code**: `make format` to fix Black and Ruff issues
6. **Run full checks**: `make check` to validate quality standards
7. **Test changes**: `make test` to ensure functionality
8. **Verify no conflicts remain**: `git status` should show clean working directory
9. **Commit only when all checks pass** - no exceptions

### Documentation Updates
- Update relevant documentation when making changes
- Ensure README and other docs reflect current functionality
- Update environment variable documentation when needed
- Update dependency documentation if adding new packages
