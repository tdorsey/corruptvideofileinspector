# Development Standards and Agent Guidelines

This document provides comprehensive development standards, coding practices, and command reference for working with the corruptvideofileinspector repository. These guidelines help ensure consistency, quality, and efficient collaboration across the project.

## Table of Contents

- [Atomic Commits (Conventional Commits 2.0)](#atomic-commits-conventional-commits-20)
- [Coding Standards](#coding-standards)
- [Command Examples](#command-examples)

---

## Atomic Commits (Conventional Commits 2.0)

### Overview

This repository strictly follows the [Conventional Commits 2.0](https://www.conventionalcommits.org/) specification. All commits must be atomic, focused, and follow the standard format.

### Single Responsibility Principle

Each commit should represent **one complete unit of work**:
- ✅ Addresses a single concern or change
- ✅ Can be understood in isolation
- ✅ Leaves the codebase in a working state
- ✅ Can be reverted without unwanted side effects
- ❌ Does not combine multiple unrelated changes
- ❌ Does not leave the codebase in a broken state

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Type** must be one of:
- `feat` - New feature or enhancement
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style/formatting (no logic changes)
- `refactor` - Code refactoring without functional changes
- `perf` - Performance improvements
- `test` - Test additions or improvements
- `chore` - Maintenance tasks, dependencies, tooling
- `ci` - CI/CD configuration changes
- `revert` - Revert previous changes

**Scope** (optional) specifies the module or component:
- `ralph`, `cli`, `scanner`, `config`, `api`, `web`, etc.

**Description** rules:
- Use imperative mood ("add" not "added")
- Start with lowercase letter
- No period at the end
- Maximum 72 characters
- Be specific and descriptive

### Atomic Requirements

#### 1. Single Unit of Work
A commit should contain all changes necessary for one logical unit of work and nothing more.

**✅ Good examples:**
```bash
feat(ralph): add single-run wrapper script
fix(scanner): resolve timeout in deep scan mode
docs(api): update GraphQL schema documentation
test(config): add validation tests for prd.json
chore(deps): update Python dependencies to latest versions
```

**❌ Bad examples:**
```bash
feat: add ralph and update docs  # Multiple concerns
fix: update config and documentation  # Mixed types
chore: various updates  # Too vague
feat(ralph): add wrapper and fix bug and update docs  # Multiple changes
```

#### 2. Revertible Without Side Effects
Any commit should be revertible using `git revert` without causing issues in unrelated areas.

**Example:** If you need to revert a feature addition, reverting that commit should not also revert unrelated documentation updates or bug fixes.

#### 3. Self-Contained
A commit should include all necessary files for the change to be complete:
- Source code changes
- Related test updates
- Configuration updates
- Documentation updates (if directly related)

**✅ Good example:**
```bash
# Commit includes implementation, tests, and config
feat(config): add validation for required fields
- Add validation module with schema definitions
- Add unit tests for all validation scenarios  
- Update config.sample.yaml with examples
```

**❌ Bad example:**
```bash
# Implementation in one commit, tests in another
feat(config): add validation module
# Later...
test(config): add tests for validation  # Should be in same commit
```

#### 4. Leaves Codebase in Working State
After each commit, the codebase should:
- ✅ Build successfully
- ✅ Pass all existing tests
- ✅ Not introduce syntax errors
- ✅ Maintain type safety (if applicable)
- ✅ Follow code quality standards

### Commit Examples by Type

#### Feature Addition (`feat`)
```bash
feat(cli): add incremental scan option
feat(api): implement GraphQL endpoint for scan history
feat(ralph): add iteration wrapper script with progress tracking
feat(scanner): implement parallel video processing
```

#### Bug Fix (`fix`)
```bash
fix(scanner): resolve memory leak in video processing
fix(config): handle missing optional fields gracefully
fix(ralph): correct submodule path in update script
fix(api): return proper error codes for validation failures
```

#### Documentation (`docs`)
```bash
docs(ralph): add comprehensive setup instructions
docs(api): update endpoint examples with authentication
docs: add troubleshooting section to main README
docs(config): document environment variable precedence
docs(agents): create new issue creation agent
docs(agents): update lint-error agent with new capabilities
```

**IMPORTANT: Agent Changes are Documentation**

Changes to GitHub Copilot agents and skills are **contributor documentation**, not user-facing features:
- Agent files in `.github/agents/` should use `docs(agents):` type
- Skill files in `.github/skills/` should use `docs(skills):` type
- Agent-related instructions should use `docs(agents):` or `docs(copilot):` type

**Why?** Agents and skills are development tools that help contributors work more effectively. They don't add features to the application itself—they document how to use GitHub Copilot to contribute to the project.

**✅ Correct:**
```bash
docs(agents): add issue creation agent
docs(agents): update lint-error agent with error detection improvements
docs(skills): add issue creation skill documentation
docs(copilot): update agent usage guidelines
```

**❌ Incorrect:**
```bash
feat(agents): add issue creation agent  # Wrong - not a user-facing feature
feat: create lint-error agent  # Wrong - agents are contributor docs
```

#### Code Style (`style`)
```bash
style(scanner): fix import organization per project standards
style: apply black formatting to all Python files
style(api): adjust line length to 79 characters
```

#### Refactoring (`refactor`)
```bash
refactor(scanner): extract validation logic into separate module
refactor(config): simplify configuration loading flow
refactor(ralph): consolidate error handling in scripts
```

#### Performance (`perf`)
```bash
perf(scanner): optimize video scanning algorithm
perf(api): add database query indexing
perf(config): cache parsed configuration
```

#### Tests (`test`)
```bash
test(scanner): add integration tests for hybrid mode
test(config): increase coverage for edge cases
test(ralph): add validation tests for prd.json format
```

#### Chores (`chore`)
```bash
chore(deps): update Python dependencies to latest versions
chore(ralph): update submodule to v1.2.0
chore: clean up temporary test files
chore(ci): update GitHub Actions to latest versions
```

#### CI/CD (`ci`)
```bash
ci(ralph): add submodule initialization to workflows
ci: enable parallel test execution
ci: add release automation workflow
```

### Breaking Changes

If a commit introduces breaking changes, add `BREAKING CHANGE:` in the footer:

```bash
feat(api): change authentication to OAuth2

BREAKING CHANGE: API now requires OAuth2 tokens instead of API keys.
Clients must update their authentication method.
```

### Multi-Paragraph Body

Use the body for context, motivation, and implementation details:

```bash
feat(scanner): add incremental scan support

Incremental scanning skips recently scanned healthy files to improve
performance on large video libraries. Files are considered "recent" if
scanned within the last 30 days (configurable).

Implementation uses a SQLite database to track scan history with
timestamp-based queries for efficient lookups. The feature is opt-in
via the --incremental flag.
```

### References and Footers

Reference issues, PRs, or related commits:

```bash
fix(scanner): resolve timeout in deep scan mode

Fixes #123
Related to #115
See also commit abc1234
```

---

## Coding Standards

### Repository Organization

#### File Structure Principles
- **Modular design**: Group related functionality in focused modules
- **Clear boundaries**: Separate concerns (business logic, presentation, configuration)
- **Consistent naming**: Follow established patterns across the codebase
- **Logical hierarchy**: Organize files in a way that reflects their purpose

#### Monorepo Structure
```
corruptvideofileinspector/
├── apps/               # Applications (cli, api, web)
│   ├── api/           # API application
│   ├── cli/           # CLI application  
│   └── web/           # Web UI application
├── libs/              # Shared libraries
│   ├── core/          # Core business logic
│   └── ui-components/ # Shared UI components
├── tools/             # Development tools
│   └── ralph/         # Ralph autonomous development tool
├── docs/              # Documentation
├── tests/             # Test suites
└── .github/           # GitHub configuration and workflows
```

#### Naming Conventions
- **Python files**: `snake_case.py` (e.g., `video_scanner.py`)
- **Python classes**: `PascalCase` (e.g., `VideoScanner`)
- **Python functions**: `snake_case()` (e.g., `scan_directory()`)
- **Configuration files**: `kebab-case.yaml` (e.g., `config.sample.yaml`)
- **Scripts**: `kebab-case.sh` (e.g., `run-ralph-once.sh`)
- **Documentation**: `UPPERCASE.md` or `PascalCase.md` (e.g., `README.md`, `SETUP.md`)

### Code Review Expectations

#### What Makes a Good PR

**Structure:**
- ✅ Focused on a single feature or fix
- ✅ Reasonable size (< 500 lines changed when possible)
- ✅ Atomic commits with clear messages
- ✅ Includes tests for new functionality
- ✅ Updates relevant documentation

**Quality:**
- ✅ Passes all CI checks (lint, format, type check, tests)
- ✅ Follows existing code patterns
- ✅ Includes error handling
- ✅ Has proper logging where appropriate
- ✅ Maintains or improves test coverage

**Documentation:**
- ✅ PR description explains the "why"
- ✅ Links to related issue(s)
- ✅ Notes any breaking changes
- ✅ Includes example usage (if applicable)

#### When to Split Commits

Split commits when changes address different concerns:

**✅ Split into separate commits:**
```bash
# Commit 1: Add feature
feat(scanner): add incremental scan support

# Commit 2: Add tests
test(scanner): add tests for incremental scan

# Commit 3: Update docs
docs(scanner): document incremental scan usage
```

**Alternative (preferred if changes are tightly coupled):**
```bash
# Single commit with all related changes
feat(scanner): add incremental scan support
- Implement incremental scanning logic
- Add comprehensive test coverage
- Update documentation with usage examples
```

**Rule of thumb:** If the changes can be reviewed and understood together, keep them in one commit. If they address separate concerns, split them.

#### How to Structure Commit History

**Linear history** (preferred for feature branches):
```
feat(scanner): add parallel processing
feat(scanner): add progress reporting  
feat(scanner): add error recovery
docs(scanner): document new features
```

**Feature commits** (for complex features):
```
feat(api)!: redesign authentication system
feat(api): implement OAuth2 provider
feat(api): add token refresh mechanism
feat(api): migrate existing users
docs(api): update authentication guide
```

### Branch Atomicity

#### One Feature Per Branch
Each branch should focus on a single feature, fix, or improvement:

**✅ Good branch names:**
- `feat/add-ralph-tool` - One feature
- `fix/scanner-timeout` - One bug fix
- `docs/update-agents-standards` - One documentation update

**❌ Bad branch names:**
- `feat/add-ralph-and-fix-bugs` - Multiple concerns
- `updates` - Too vague
- `john-work` - Non-descriptive

#### Independent Merge Capability
Each branch should be independently mergeable:
- ✅ Can be merged without dependencies on other branches
- ✅ Can be merged in any order relative to other branches
- ✅ Doesn't break functionality when merged alone
- ❌ Requires another branch to be merged first
- ❌ Conflicts with parallel development

#### Rollback Considerations
Design branches to be easily revertible:
- ✅ Reverting the branch doesn't break unrelated features
- ✅ Configuration changes are backwards compatible (when possible)
- ✅ Database migrations are reversible
- ❌ Deletes or modifies shared code without safeguards

### Commit Granularity

#### When to Create Separate Commits

Create separate commits when:
1. **Different types of changes**: Feature vs. bug fix vs. documentation
2. **Different modules**: Scanner vs. API vs. Web UI
3. **Sequential dependencies**: Must be applied in order
4. **Logical checkpoints**: Milestone in feature development

#### How to Group Related Changes

Group changes in one commit when they:
1. **Implement one feature**: All code for a single feature
2. **Fix one bug**: Root cause fix plus related test updates
3. **Refactor one module**: All changes for a cohesive refactoring
4. **Update one document**: Related documentation changes

#### Balance Between Atomic and Practical

**Too granular** (❌):
```bash
feat(scanner): add function signature
feat(scanner): implement function body
feat(scanner): add docstring
test(scanner): add test file
test(scanner): add first test
test(scanner): add second test
```

**Too coarse** (❌):
```bash
feat: implement entire scanning system with tests and docs
```

**Just right** (✅):
```bash
feat(scanner): implement incremental scanning
test(scanner): add incremental scan tests
docs(scanner): document incremental scan feature
```

---

## Command Examples

### Nx Command Patterns

#### Running Targets
```bash
# Run a specific target for a project
nx run <project>:<target>

# Examples
nx run ralph:once                    # Run Ralph once
nx run cli:build                     # Build CLI
nx run web:test                      # Test web UI
nx run api:lint                      # Lint API code

# Shorthand (when no conflicts)
nx <target> <project>
nx test api
nx build web
```

#### Passing Parameters
```bash
# Pass parameters to targets
nx run <project>:<target> --param=value

# Examples
nx run ralph:iterate --iterations=20
nx run web:serve --port=4200
nx run api:test --coverage=true
nx run cli:build --prod=true

# Multiple parameters
nx run ralph:iterate --iterations=20 --verbose=true
```

#### Affected Commands
```bash
# Run commands only for affected projects
nx affected:<target>

# Examples
nx affected:test        # Test only affected projects
nx affected:build       # Build only affected projects
nx affected:lint        # Lint only affected projects

# With base comparison
nx affected:test --base=main
nx affected:build --base=origin/main --head=HEAD
```

#### Graph Visualization
```bash
# Visualize project dependency graph
nx graph

# Show dependency graph for specific project
nx graph --focus=ralph

# Show affected projects graph
nx affected:graph

# Export graph to file
nx graph --file=output.html
```

#### Workspace Commands
```bash
# List all projects
nx show projects

# Show project details
nx show project ralph

# Run command for all projects
nx run-many --target=test --all

# Run command for specific projects
nx run-many --target=build --projects=cli,api

# Clear Nx cache
nx reset

# Print Nx workspace info
nx report
```

### Submodule Operations

#### Clone with Submodules
```bash
# Clone repository with all submodules
git clone --recurse-submodules <url>

# Example
git clone --recurse-submodules https://github.com/TDorsey/corruptvideoinspector.git

# Clone with submodules at specific depth
git clone --recurse-submodules --depth=1 <url>
```

#### Initialize Submodules
```bash
# Initialize all submodules in existing repository
git submodule update --init --recursive

# Initialize specific submodule
git submodule update --init tools/ralph/ralph-cli

# Initialize and fetch latest
git submodule update --init --remote --recursive
```

#### Update Submodule
```bash
# Update submodule to latest commit in tracked branch
git submodule update --remote <path>

# Example
git submodule update --remote tools/ralph/ralph-cli

# Update all submodules
git submodule update --remote --merge

# Update and rebase
git submodule update --remote --rebase
```

#### Check Submodule Status
```bash
# Show status of all submodules
git submodule status

# Show detailed submodule info
git submodule

# Show submodule summary
git submodule summary

# Check which commit submodule is on
cd tools/ralph/ralph-cli
git describe --tags --exact-match  # If on a tag
git log --oneline -1                # Show current commit
```

#### Working with Submodule Changes
```bash
# Make changes in submodule
cd tools/ralph/ralph-cli
git fetch --tags
git checkout v1.2.0
cd ../../..

# Commit submodule update in main repository
git add tools/ralph/ralph-cli
git commit -m "chore(ralph): update submodule to v1.2.0"

# Push changes (submodule must be pushed first if you made changes)
cd tools/ralph/ralph-cli
git push  # If you made changes in submodule
cd ../../..
git push  # Push main repository
```

### CI/CD Interactions

#### How CI Validates Commits
```yaml
# CI checks performed on each commit
1. Checkout code (with submodules)
2. Validate commit messages (Conventional Commits)
3. Validate PR title (if pull request)
4. Check code formatting (Black, Prettier)
5. Run linters (Ruff, ESLint)
6. Type checking (MyPy, TypeScript)
7. Security scanning (Bandit, npm audit)
8. Run tests (pytest, Jest)
9. Build artifacts (Python package, Docker image)
10. Validate submodule pinning (Ralph specific)
```

#### Running Checks Locally Before Push
```bash
# Run all quality checks
make check
# Equivalent to: make format && make lint && make type

# Run tests
make test

# Run specific checks
make format     # Format code with Black
make lint       # Lint with Ruff
make type       # Type check with MyPy

# Python-specific checks
black src/ tests/
ruff check src/ tests/
mypy src/ tests/
pytest tests/

# Web-specific checks
npm run lint
npm run format
npm test
```

#### CI Commands for Affected Projects
```bash
# CI uses Nx affected commands to optimize builds
# Only test projects affected by changes

# In CI (automatically uses PR base)
nx affected:test

# Locally (compare with main)
nx affected:test --base=origin/main

# See what will be affected
nx affected:graph --base=origin/main
nx show affected --base=origin/main
```

### Common Workflows

#### Feature Development Flow
```bash
# 1. Create feature branch
git checkout -b feat/new-feature main

# 2. Make changes in atomic commits
git add <files>
git commit -m "feat(module): add new functionality"

# 3. Run checks locally
make check
make test

# 4. Push branch
git push -u origin feat/new-feature

# 5. Create pull request
gh pr create --title "feat(module): add new functionality" \
             --body "Implements #123\n\nAdds new feature..."

# 6. Address review feedback with new commits
git add <files>
git commit -m "fix(module): address review feedback"
git push

# 7. After approval, merge via GitHub UI
# (or using gh CLI)
gh pr merge --squash  # or --merge, --rebase
```

#### Hotfix Process
```bash
# 1. Create hotfix branch from main
git checkout -b fix/critical-bug main

# 2. Implement fix
git add <files>
git commit -m "fix(module): resolve critical security issue"

# 3. Test thoroughly
make test

# 4. Push and create PR
git push -u origin fix/critical-bug
gh pr create --title "fix(module): resolve critical security issue" \
             --body "Fixes #456\n\nSecurity: ..." \
             --label "priority:high,type:security"

# 5. After review, merge immediately
gh pr merge --squash

# 6. Verify deployment
git checkout main
git pull
```

#### Dependency Update Workflow
```bash
# 1. Create update branch
git checkout -b chore/update-dependencies main

# 2. Update Python dependencies
poetry update
poetry lock --no-update  # Or full update

# 3. Update Node dependencies  
npm update
npm audit fix  # Address security issues

# 4. Run tests to verify compatibility
make test
npm test

# 5. Commit with detailed message
git add poetry.lock package.json package-lock.json
git commit -m "chore(deps): update dependencies to latest versions

Updated packages:
- package-a: 1.0.0 -> 1.1.0
- package-b: 2.0.0 -> 2.1.0

All tests pass with new versions."

# 6. Create PR
git push -u origin chore/update-dependencies
gh pr create --title "chore(deps): update dependencies to latest versions" \
             --body "Updates dependencies to latest compatible versions..."
```

#### Working with Submodules
```bash
# 1. Update submodule to latest release
cd tools/ralph/ralph-cli
git fetch --tags
LATEST=$(gh release view --repo TDorsey/ralph --json tagName -q .tagName)
git checkout ${LATEST}
cd ../../..

# 2. Test with new version
nx run ralph:once  # Test single run

# 3. Commit submodule update
git add tools/ralph/ralph-cli
git commit -m "chore(ralph): update submodule to ${LATEST}"

# 4. Push update
git push
```

#### Reverting Changes
```bash
# Revert a specific commit
git revert <commit-hash>

# Revert last commit
git revert HEAD

# Revert without committing (to make changes first)
git revert --no-commit <commit-hash>

# Revert a merge commit
git revert -m 1 <merge-commit-hash>

# Push reverted changes
git push
```

---

## Best Practices Summary

### Commits
- ✅ One logical change per commit
- ✅ Atomic and revertible
- ✅ Follow Conventional Commits format
- ✅ Leave codebase in working state
- ✅ Include related tests and docs

### Branches
- ✅ One feature per branch
- ✅ Independently mergeable
- ✅ Descriptive names with type prefix
- ✅ Based on latest main
- ✅ Keep reasonably small (< 500 lines when possible)

### Code Quality
- ✅ Run `make check` before committing
- ✅ Ensure tests pass locally
- ✅ Follow existing code patterns
- ✅ Add tests for new functionality
- ✅ Update documentation

### Collaboration
- ✅ Reference issues in commits and PRs
- ✅ Provide context in PR descriptions
- ✅ Respond to review feedback promptly
- ✅ Keep PRs focused and reviewable
- ✅ Use draft PRs for work in progress

---

## Additional Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Git Documentation](https://git-scm.com/doc)
- [Nx Documentation](https://nx.dev)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Repository Contributing Guide](CONTRIBUTING.md)
- [Ralph Tool Documentation](../tools/ralph/README.md)
