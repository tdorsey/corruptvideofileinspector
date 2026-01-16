---
name: ralph
description: Run Ralph autonomous development tool to implement features from a Product Requirements Document (prd.json). Use when asked to run Ralph, execute automated development iterations, or implement work items from a backlog using Copilot CLI.
license: MIT
compatibility: Requires GitHub Copilot CLI, git submodule at tools/ralph/ralph-cli
metadata:
  author: tdorsey
  version: "1.0"
---

# Ralph Autonomous Development Tool

Ralph runs GitHub Copilot CLI in iterative loops to implement features automatically from a Product Requirements Document (prd.json).

## When to Use

Use this skill when:
- The user asks to run Ralph or execute automated development
- The user wants to implement work items from a backlog
- The user mentions processing prd.json or Product Requirements Document
- The user asks about iterative feature implementation

## Prerequisites

Before running Ralph, verify:

1. **Ralph submodule is initialized**:
   ```bash
   ls tools/ralph/ralph-cli/ralph.sh
   ```

2. **Copilot CLI is available**:
   ```bash
   copilot --version
   ```

3. **Work items exist in prd.json**:
   ```bash
   cat tools/ralph/config/prd.json
   ```

## Running Ralph

### Single Iteration

Run one iteration to implement a single work item:

```bash
nx run ralph:once
```

### Multiple Iterations

Run multiple iterations (default 10):

```bash
nx run ralph:iterate
nx run ralph:iterate --iterations=20
```

### Update Ralph

Update to the latest Ralph release:

```bash
nx run ralph:update
```

## Work Item Format

Work items in `tools/ralph/config/prd.json` follow this structure:

```json
[
  {
    "category": "Feature Name",
    "description": "Detailed description of what needs to be implemented",
    "steps": [
      "Step 1: First action to take",
      "Step 2: Second action to take"
    ],
    "passes": [
      "Criterion 1: How to verify success",
      "Criterion 2: Another success criterion"
    ]
  }
]
```

## Progress Tracking

Ralph tracks progress in `tools/ralph/progress.txt`. Review after iterations:

```bash
cat tools/ralph/progress.txt
git diff tools/ralph/progress.txt
```

## Safety Guidelines

1. **Always work on a feature branch** - never run Ralph on main
2. **Commit your work before running Ralph** - Ralph makes automatic commits
3. **Review Ralph's commits before pushing**:
   ```bash
   git log --oneline origin/main..HEAD
   ```
4. **Run quality checks after Ralph sessions**:
   ```bash
   make check
   make test
   ```

## Reverting Changes

If Ralph makes unwanted changes:

```bash
# Revert last commit
git reset --hard HEAD~1

# Revert multiple commits
git reset --hard HEAD~10
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Submodule not found | `git submodule update --init --recursive` |
| Copilot CLI not found | Install from https://githubnext.com/projects/copilot-cli |
| prd.json not found | Create or restore: `git checkout tools/ralph/config/prd.json` |
| Nx target not found | Run `nx reset` then retry |

## Related Files

- [tools/ralph/README.md](tools/ralph/README.md) - Full documentation
- [tools/ralph/SETUP.md](tools/ralph/SETUP.md) - Setup instructions
- [tools/ralph/config/prd.json](tools/ralph/config/prd.json) - Work items
- [tools/ralph/progress.txt](tools/ralph/progress.txt) - Progress tracking
