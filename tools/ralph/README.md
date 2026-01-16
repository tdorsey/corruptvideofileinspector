# Ralph - Autonomous Development Tool

Ralph is an autonomous development tool that runs GitHub Copilot CLI in iterative loops to implement repository tasks automatically. This integration brings Ralph into the corruptvideofileinspector monorepo as an Nx project.

## Purpose

Ralph automates feature implementation by:
- Reading work items from a Product Requirements Document (prd.json)
- Using GitHub Copilot CLI to understand and implement each work item
- Making code changes autonomously
- Automatically committing completed work
- Tracking progress through multiple iterations

This is particularly useful for:
- Implementing features from a backlog systematically
- Batch processing multiple small tasks
- Maintaining consistent coding standards through AI-assisted development
- Reducing manual implementation time for well-defined work items

## Architecture

### Submodule Structure
```
tools/ralph/
├── ralph-cli/          # Git submodule (read-only, third-party code)
│   ├── ralph.sh        # Main iteration script
│   ├── ralph-once.sh   # Single iteration script
│   ├── plans/          # Ralph's planning templates
│   └── prompts/        # Ralph's AI prompts
├── config/
│   └── prd.json        # Work items configuration
├── scripts/
│   ├── run-ralph-once.sh         # Single iteration wrapper
│   ├── run-ralph-iterations.sh   # Multiple iterations wrapper
│   └── update-ralph.sh           # Submodule update script
├── progress.txt        # Progress tracking (version controlled)
├── project.json        # Nx project configuration
└── README.md          # This file
```

**Important**: The `ralph-cli/` submodule contains upstream Ralph code from TDorsey/ralph. It is:
- **Read-only**: Do not modify submodule contents directly
- **Release-pinned**: Always pinned to a specific release tag (not branch HEAD)
- **Third-party**: Maintained separately from this repository

## Prerequisites

Before using Ralph, ensure you have:

1. **GitHub Copilot CLI** installed and authenticated
   ```bash
   # Install: https://githubnext.com/projects/copilot-cli
   copilot --version
   ```

2. **GitHub CLI (gh)** installed and authenticated (for updates)
   ```bash
   gh auth status
   ```

3. **Ralph submodule** initialized
   ```bash
   # When cloning the repository
   git clone --recurse-submodules <repo-url>
   
   # Or in existing clone
   git submodule update --init --recursive
   ```

4. **Active GitHub Copilot subscription**
   - Ralph uses Copilot CLI's default model configuration
   - Ensure your subscription is active and the CLI is authenticated

## Setup

### Initial Setup (New Clone)

If you're cloning the repository for the first time:

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/TDorsey/corruptvideoinspector.git
cd corruptvideoinspector

# Verify submodule is initialized
git submodule status
# Should show: <commit-hash> tools/ralph/ralph-cli (tag-name)
```

### Setup in Existing Clone

If you already have the repository cloned:

```bash
# Initialize the Ralph submodule
git submodule update --init --recursive

# Verify submodule status
cd tools/ralph/ralph-cli
git describe --tags --exact-match
# Should show a release tag like: v1.0.0

cd ../../..
```

### Verify Installation

```bash
# Check that Ralph scripts are executable
ls -l tools/ralph/scripts/*.sh

# Verify copilot CLI is available
copilot --version

# Check Nx can find the ralph project
nx show project ralph
```

## Configuration

### Product Requirements Document (prd.json)

Ralph reads work items from `config/prd.json`. This file follows the upstream Ralph format:

```json
[
  {
    "category": "Feature Name",
    "description": "Detailed description of what needs to be implemented",
    "steps": [
      "Step 1: First action to take",
      "Step 2: Second action to take",
      "Step 3: Third action to take"
    ],
    "passes": [
      "Criterion 1: How to verify success",
      "Criterion 2: Another success criterion",
      "Criterion 3: Final validation check"
    ]
  }
]
```

**Fields**:
- `category`: High-level name/category for the work item
- `description`: Detailed explanation of the task
- `steps`: Ordered list of implementation steps
- `passes`: Success criteria for validation

**Example Work Item**:
```json
{
  "category": "Add Configuration Validation",
  "description": "Implement validation for the config.yaml file to ensure all required fields are present and properly formatted before the application starts",
  "steps": [
    "Create a validation module in src/config/validator.py",
    "Add schema definitions for each configuration section",
    "Implement validation functions with clear error messages",
    "Add unit tests for validation logic",
    "Integrate validation into application startup"
  ],
  "passes": [
    "All required fields are validated at startup",
    "Invalid configurations produce clear error messages",
    "Unit tests cover all validation scenarios",
    "Application fails fast with invalid config"
  ]
}
```

### Editing Work Items

1. Edit `tools/ralph/config/prd.json`
2. Add, modify, or remove work items
3. Commit changes to version control
4. Run Ralph to process updated work items

```bash
# Edit prd.json
vim tools/ralph/config/prd.json

# Commit changes
git add tools/ralph/config/prd.json
git commit -m "feat(ralph): add new work items for feature X"

# Run Ralph
nx run ralph:once
```

## Usage

Ralph is integrated into the Nx workspace with three main targets:

### 1. Single Iteration (`ralph:once`)

Execute a single Ralph iteration. Ralph will:
- Read the next work item from prd.json
- Implement the work item using Copilot CLI
- Commit changes automatically
- Update progress.txt

```bash
# Run single iteration
nx run ralph:once

# Or using shorthand
nx ralph:once
```

**Use case**: Testing Ralph with a new work item, debugging, or running incrementally with manual review between iterations.

### 2. Multiple Iterations (`ralph:iterate`)

Execute multiple Ralph iterations in sequence. Each iteration processes one work item.

```bash
# Run 10 iterations (default)
nx run ralph:iterate

# Run specific number of iterations
nx run ralph:iterate --iterations=20
nx run ralph:iterate --iterations=5

# Or using shorthand
nx ralph:iterate --iterations=15
```

**Use case**: Batch processing multiple work items unattended, implementing a backlog of features overnight.

### 3. Update Ralph (`ralph:update`)

Update the Ralph submodule to the latest release tag from TDorsey/ralph.

```bash
# Update to latest release
nx run ralph:update

# Or using shorthand
nx ralph:update
```

After updating:
```bash
# Verify new version
cd tools/ralph/ralph-cli
git describe --tags --exact-match

# Commit the submodule update
cd ../../..
git add tools/ralph/ralph-cli
git commit -m "chore(ralph): update submodule to v1.2.0"
git push
```

## Progress Tracking

Ralph tracks progress in `progress.txt`, which is version controlled. This file records:
- Iteration timestamps
- Work items completed
- Success/failure status
- Relevant notes from each iteration

After each iteration, review `progress.txt` to see what Ralph accomplished:

```bash
# View progress
cat tools/ralph/progress.txt

# View recent changes
git diff tools/ralph/progress.txt
```

## Nx Integration

Ralph uses Nx environment variables for proper workspace context:

- `NX_WORKSPACE_ROOT`: Repository root directory
- `NX_PROJECT_ROOT`: Ralph project directory (tools/ralph)

These variables are automatically available when running Ralph through Nx targets. The wrapper scripts use these variables to:
- Navigate to correct directories
- Reference configuration files
- Execute Ralph with proper context

## Common Workflows

### Implementing a Feature Backlog

1. **Prepare work items**
   ```bash
   # Edit prd.json with your backlog
   vim tools/ralph/config/prd.json
   
   # Commit the work items
   git add tools/ralph/config/prd.json
   git commit -m "feat(ralph): add Q1 feature backlog"
   ```

2. **Commit your current work**
   ```bash
   # Ensure working directory is clean
   git status
   git add .
   git commit -m "feat: save work before ralph session"
   ```

3. **Run Ralph iterations**
   ```bash
   # Process multiple work items
   nx run ralph:iterate --iterations=20
   ```

4. **Review Ralph's commits**
   ```bash
   # See what Ralph committed
   git log --oneline -20
   
   # Review changes
   git diff HEAD~20
   ```

5. **Post-process if needed**
   ```bash
   # Run formatters/linters on Ralph's code
   make check
   
   # Run tests
   make test
   
   # Fix any issues Ralph may have missed
   # Commit fixes separately
   ```

### Testing a Single Work Item

1. **Add work item to prd.json**
2. **Run single iteration**
   ```bash
   nx run ralph:once
   ```
3. **Review changes**
   ```bash
   git show HEAD
   git diff HEAD~1
   ```
4. **Revert if unsatisfied**
   ```bash
   git reset --hard HEAD~1
   ```

### Updating Ralph Version

```bash
# Update to latest release
nx run ralph:update

# Test with single iteration
nx run ralph:once

# If successful, commit submodule update
git add tools/ralph/ralph-cli
git commit -m "chore(ralph): update to latest release"
git push
```

## Safety Considerations

### Ralph Can Push Commits

Ralph has the ability to automatically commit and potentially push changes. To stay safe:

1. **Work on a feature branch**
   ```bash
   git checkout -b feature/ralph-batch-implementation
   ```

2. **Commit your work before running Ralph**
   ```bash
   git add .
   git commit -m "feat: save work before ralph"
   ```

3. **Review Ralph's commits before pushing**
   ```bash
   # See what Ralph did
   git log --oneline origin/main..HEAD
   
   # Review changes
   git diff origin/main
   ```

4. **Use single iterations for testing**
   ```bash
   # Test with one iteration first
   nx run ralph:once
   git show HEAD
   ```

### Reverting Ralph Changes

If Ralph makes unwanted changes:

```bash
# Revert last commit
git reset --hard HEAD~1

# Revert multiple commits
git reset --hard HEAD~10

# Or use interactive rebase
git rebase -i HEAD~10
```

### Best Practices

- ✅ **DO** commit your work before running Ralph
- ✅ **DO** use feature branches for Ralph sessions
- ✅ **DO** review Ralph's commits before pushing
- ✅ **DO** run linters/formatters after Ralph sessions
- ✅ **DO** test Ralph's changes thoroughly
- ❌ **DON'T** run Ralph on main branch directly
- ❌ **DON'T** run Ralph with uncommitted changes
- ❌ **DON'T** trust Ralph blindly - always review

## Post-Processing

Ralph generates functional code, but it should follow existing project standards:

```bash
# After Ralph session, run project quality checks
make check          # Format, lint, type check
make test          # Run tests
make format        # Format code

# Or individual tools
black src/
ruff check src/
mypy src/
pytest tests/
```

If Ralph's code doesn't meet standards:
1. Fix issues manually or with automated tools
2. Commit fixes in a separate commit
3. Maintain Ralph's commits in history for traceability

## Troubleshooting

### "Ralph submodule not found"

```bash
# Initialize submodules
git submodule update --init --recursive

# Verify
ls -la tools/ralph/ralph-cli
```

### "GitHub Copilot CLI not found"

```bash
# Install Copilot CLI
# Visit: https://githubnext.com/projects/copilot-cli

# Verify installation
copilot --version

# Authenticate if needed
gh auth login
```

### "config/prd.json not found"

```bash
# Create or restore prd.json
# It may have been accidentally deleted or not committed

# Check if it exists
ls tools/ralph/config/prd.json

# If missing, restore from git
git checkout tools/ralph/config/prd.json

# Or create a new one from the example above
```

### Ralph fails during iteration

1. **Check progress.txt** for error details
   ```bash
   cat tools/ralph/progress.txt
   ```

2. **Verify prerequisites**
   ```bash
   copilot --version
   gh auth status
   git submodule status
   ```

3. **Check work item format** in prd.json
   - Ensure JSON is valid
   - Verify all required fields are present
   - Check for clear, actionable steps

4. **Review Copilot subscription**
   - Ensure subscription is active
   - Check rate limits haven't been exceeded

### Nx target not found

```bash
# Verify Nx can see the project
nx show project ralph

# If not found, ensure project.json exists
ls -la tools/ralph/project.json

# Rebuild Nx cache
nx reset
```

### Submodule not on release tag

```bash
# Check current state
cd tools/ralph/ralph-cli
git describe --tags

# If on a branch, checkout latest release
git fetch --tags
LATEST=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $LATEST

# Return and commit
cd ../../..
git add tools/ralph/ralph-cli
git commit -m "fix(ralph): pin submodule to release tag"
```

## Advanced Usage

### Custom Copilot Model

Ralph uses Copilot CLI's default model. To change it:

```bash
# Configure copilot CLI before running Ralph
copilot config set model gpt-4

# Then run Ralph normally
nx run ralph:once
```

### Parallel Work Items

Ralph processes work items sequentially. For parallel processing:
1. Split prd.json into multiple files
2. Run Ralph in separate feature branches
3. Merge branches when complete

### Integration with CI/CD

Ralph can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/ralph.yml
name: Ralph Nightly Build
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
  workflow_dispatch:

jobs:
  ralph:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive
      
      - name: Setup Copilot CLI
        run: |
          # Install copilot CLI
          # Authenticate with secrets
      
      - name: Run Ralph
        run: nx run ralph:iterate --iterations=10
      
      - name: Create PR
        run: |
          # Create PR with Ralph's changes
```

## Contributing

To improve Ralph integration in this repository:

1. **For Ralph-specific changes**: Submit issues/PRs to upstream Ralph repository
2. **For integration changes**: Submit PRs to this repository
3. **For new work items**: Edit prd.json and commit to this repository

## Related Documentation

- [Nx Documentation](https://nx.dev)
- [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli)
- [Ralph Repository](https://github.com/TDorsey/ralph)
- [Conventional Commits](https://www.conventionalcommits.org/)

## Support

For issues with:
- **Ralph integration**: Open issue in this repository
- **Ralph itself**: Open issue in TDorsey/ralph repository
- **Copilot CLI**: Contact GitHub Support or Copilot team
- **Work item format**: See examples in config/prd.json and upstream Ralph docs

## License

- **Ralph** (submodule): Licensed under its own terms (see ralph-cli/LICENSE)
- **This integration**: Licensed under the same terms as the parent repository
