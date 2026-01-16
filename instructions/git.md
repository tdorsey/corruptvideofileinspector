# Git & Version Control

## Commit Conventions, Branching Strategies, and Version Control

### Commit Standards (REQUIRED)

**All commits MUST follow the [Conventional Commits](https://www.conventionalcommits.org/) standard:**

#### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Valid Types
- `feat`: New features and enhancements
- `fix`: Bug fixes
- `docs`: Documentation changes
- `style`: Code style changes (formatting, whitespace)
- `refactor`: Code refactoring without behavior changes
- `perf`: Performance improvements
- `test`: Test additions or modifications
- `chore`: Maintenance tasks, dependencies, tooling

#### Description Format
- **After the type and scope, the brief description should begin in lowercase**
- Use imperative mood: "add feature" not "added feature"
- No period at the end
- Maximum 72 characters for first line

#### Examples
```
feat(cli): add video scan command
fix(config): resolve YAML parsing error
docs(readme): update installation instructions
test(scanner): add unit tests for corruption detection
chore(deps): update ffmpeg to version 5.1
perf(scanner): optimize video processing pipeline
refactor(core): extract video validation logic
style(cli): format code with black
```

#### Atomic Commits
- Each commit should represent a single, focused change
- Avoid combining unrelated changes in one commit
- Makes code review easier
- Simplifies reverting changes if needed
- Improves git history clarity

### Branching Strategy

#### Branch Naming Conventions
```
<type>/<short-description>

Examples:
feat/add-trakt-sync
fix/config-validation
docs/update-readme
chore/update-dependencies
```

#### Main Branches
- **`main`**: Production-ready code
- **Feature branches**: Created from main, merged back via PR
- **Release branches**: For release preparation (if needed)

#### Branch Workflow
1. Create feature branch from main
2. Make changes with conventional commits
3. Push branch to remote
4. Open pull request
5. Address review feedback
6. Merge to main after approval

### Pull Request Requirements (REQUIRED)

**Before submitting a pull request:**

#### Merge Conflicts
- **MUST resolve all merge conflicts** before submission
- PRs with unresolved conflicts will not be accepted
- Pre-commit hook `check-merge-conflict` detects conflict markers
- Verify with `git status` and `git diff`

#### Dependencies
- **MUST update `poetry.lock`** if dependencies were modified
- Commit lock file changes with pyproject.toml changes

#### CI/CD Checks
- **MUST pass all CI/CD checks**:
  - Code formatting (black)
  - Linting (ruff)
  - Type checking (mypy)
  - Test suite (pytest)
  - Security scanning (if applicable)

#### Pre-commit Hooks
```bash
# Setup pre-commit hooks
make pre-commit-install

# Run manually
make pre-commit-run

# Hooks run automatically on commit:
# - check-merge-conflict
# - check-yaml
# - trailing-whitespace
# - end-of-file-fixer
# - mixed-line-ending
```

### Git Workflow

#### Starting New Work
```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feat/new-feature

# Or use naming convention
git checkout -b fix/bug-description
```

#### Making Commits
```bash
# Stage changes
git add <files>

# Commit with conventional message
git commit -m "feat(component): add new feature"

# Or use multi-line commit
git commit
# Opens editor for detailed message
```

#### Pushing Changes
```bash
# Push feature branch
git push origin feat/new-feature

# Push with tracking
git push -u origin feat/new-feature
```

#### Updating Branch
```bash
# Fetch latest changes
git fetch origin

# Rebase on main (recommended)
git rebase origin/main

# Or merge main into feature
git merge origin/main
```

### Resolving Merge Conflicts

#### Detection
```bash
# Check for conflicts
git status

# View conflicts
git diff

# Pre-commit hook detects markers
make pre-commit-run
```

#### Resolution Process
1. Identify conflicted files (marked by `<<<<<<<`, `=======`, `>>>>>>>`)
2. Edit files to resolve conflicts
3. Remove conflict markers
4. Test changes thoroughly
5. Stage resolved files: `git add <file>`
6. Complete merge: `git commit` or `git rebase --continue`
7. Verify: `git status` and `git diff`

#### Preventing Conflicts
- Keep branches short-lived
- Rebase frequently on main
- Coordinate with team on shared files
- Communicate large refactorings

### Git Best Practices

#### Commit Messages
- **First line**: Concise summary (conventional format)
- **Body**: Detailed explanation if needed
- **Footer**: Reference issues/PRs (`Fixes #123`)

Example:
```
feat(scanner): add parallel video processing

Implement concurrent video scanning using multiprocessing
to improve performance on large video libraries.

- Add worker pool configuration
- Implement progress tracking
- Handle errors per-video

Fixes #123
```

#### Commit Frequency
- Commit early and often
- Each commit should build/test successfully
- Logical units of work
- Easy to review and understand

#### Git History
- Keep history clean and readable
- Use interactive rebase to clean up before PR
- Squash minor fix commits
- Preserve meaningful history

### Git Commands Reference

#### Status and Info
```bash
git status                       # Show working tree status
git log --oneline               # View commit history
git log --graph --oneline       # Visual branch history
git diff                        # Show unstaged changes
git diff --staged               # Show staged changes
git show <commit>               # Show commit details
```

#### Branch Management
```bash
git branch                      # List local branches
git branch -a                   # List all branches
git branch -d <branch>          # Delete local branch
git checkout <branch>           # Switch branches
git checkout -b <branch>        # Create and switch
```

#### Stashing Changes
```bash
git stash                       # Stash current changes
git stash list                  # List stashes
git stash pop                   # Apply and remove stash
git stash apply                 # Apply but keep stash
```

#### Undoing Changes
```bash
git checkout -- <file>          # Discard local changes
git reset HEAD <file>           # Unstage file
git revert <commit>             # Revert commit
git reset --hard origin/main    # Reset to remote main
```

#### Viewing Changes
```bash
# View file at specific commit
git show <commit>:<file>

# Compare branches
git diff main..feature-branch

# Show files changed in commit
git diff-tree --no-commit-id --name-only -r <commit>
```

### Repository Maintenance

#### Cleaning Up
```bash
# Remove untracked files (dry run)
git clean -n

# Remove untracked files
git clean -f

# Remove untracked directories
git clean -fd

# Remove ignored files too
git clean -fdx
```

#### Pruning
```bash
# Prune remote tracking branches
git fetch --prune

# Remove local branches merged to main
git branch --merged main | grep -v "main" | xargs git branch -d
```

### Git Configuration

#### User Setup
```bash
# Set user name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Check configuration
git config --list
```

#### Useful Aliases
```bash
# Setup useful aliases
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
```

### Limitations in Copilot Environment

**You cannot perform these git operations:**
- Commit or push directly with git/gh commands
- Update issues (description, assignees, labels)
- Update PR descriptions
- Open new issues or PRs
- Pull branches from GitHub
- Fix merge conflicts yourself (ask user)
- Use `git reset --hard` (force push not available)
- Use `git rebase` to rewrite history (force push not available)
- Push changes to other repositories

**You can:**
- Use `git` commands to inspect repository
- Make local changes to files
- Use **report_progress** tool to commit and push changes
- Run `git status` and `git diff` to view changes

### Using report_progress Tool

#### Purpose
- Commits and pushes changes to PR
- Updates PR description with progress
- Handles git operations in Copilot environment

#### Usage
```python
report_progress(
    commitMessage="feat(scanner): add parallel processing",
    prDescription="""
    - [x] Implement worker pool
    - [x] Add progress tracking
    - [ ] Add error handling
    - [ ] Update documentation
    """
)
```

#### Best Practices
- Use conventional commit format for commitMessage
- Update checklist in prDescription
- Report progress after meaningful units of work
- Review committed files to ensure expected scope

### Pre-commit Hooks

#### Setup
```bash
# Install pre-commit hooks
make pre-commit-install

# Update hooks
pre-commit autoupdate
```

#### Hooks Configured
- **check-merge-conflict**: Detect merge conflict markers
- **check-yaml**: Validate YAML files
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **mixed-line-ending**: Consistent line endings
- **black**: Python code formatting
- **ruff**: Python linting

#### Bypassing Hooks (Use Sparingly)
```bash
# Skip pre-commit hooks (emergency only)
git commit --no-verify -m "emergency fix"
```

### Version Control Best Practices Summary
- **Use conventional commits** for all commits
- **Keep commits atomic** and focused
- **Write clear commit messages** with context
- **Resolve merge conflicts** before PR submission
- **Update dependencies properly** (poetry.lock)
- **Run pre-commit hooks** before pushing
- **Keep branches short-lived** to minimize conflicts
- **Rebase frequently** on main
- **Use report_progress** tool in Copilot environment
- **Review changes** before committing (`git diff`)
