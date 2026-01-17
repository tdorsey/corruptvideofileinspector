# Agent Tool Usage Philosophy

This document clarifies the tool usage philosophy for all GitHub Copilot agents in this repository.

## Core Principle: Flexibility Over Restriction

**All agents have access to all tools when needed to complete their work effectively.**

The tool specifications in agent files indicate PRIMARY tools (what the agent SHOULD use most often), not EXCLUSIVE tools (what they CAN ONLY use).

## Available Tools for All Agents

Every agent has access to these tools:

1. **read** - Read any file in the repository
2. **edit** - Create or modify any file
3. **search** - Search across the codebase
4. **bash** - Execute shell commands when necessary
5. **report_progress** - Commit changes and create/update PRs

## Git and Branch Management

### What All Agents CAN Do

✅ **Create feature branches** - Any agent can create a new branch for their work
✅ **Make commits** - Any agent can commit changes to their branch
✅ **Push to feature branches** - Any agent can push to their own feature branches
✅ **Create pull requests** - Any agent can create PRs from their branches
✅ **Update PR descriptions** - Via report_progress tool

### What Agents CANNOT Do

❌ **Push directly to main** - Blocked by branch protection rules (not agent restrictions)
❌ **Push to production** - Blocked by branch protection rules
❌ **Bypass required reviews** - Branch protection enforces this
❌ **Force push** - Disabled in repository settings

### How to Use Git Operations

Agents should use the **report_progress** tool for git operations:

```
report_progress(
  commitMessage="docs(architecture): add database schema design",
  prDescription="## Architecture Design\n\n- Added database schema..."
)
```

This tool safely handles:
- Creating commits with proper messages
- Pushing to the current branch
- Creating or updating PRs
- Following conventional commit standards

## Tool Usage by Agent Type

### Design/Planning Agents
**Primary tools**: read, edit, search
**Can also use**: bash (to verify file structure, check dependencies)

**Example**: Architecture Designer checking if a directory exists:
```bash
ls -la src/database/  # Verify directory structure
```

### Implementation Agents
**Primary tools**: read, edit, search, bash
**Regularly use**: bash for validation (make check, make format)

**Example**: Feature Creator validating code quality:
```bash
make check  # Run black, ruff, mypy
```

### Review Agents
**Primary tools**: read, search, bash
**Regularly use**: bash for running checks

**Example**: Code Reviewer running tests:
```bash
make test  # Verify tests pass
```

## When to Use Bash

Agents SHOULD use bash when:

1. **Validation needed** - Checking if changes work correctly
2. **Quality checks** - Running formatters, linters, type checkers
3. **Testing** - Running test suites
4. **Verification** - Confirming file existence, checking structure
5. **Build operations** - Compiling, building, packaging

Agents CAN use bash for:
- File operations (ls, cat, grep)
- Git inspection (git status, git diff, git log)
- Make targets (make check, make test, make build)
- Running pre-commit hooks
- Any other shell command that helps complete their work

## Primary vs. Available Tools

The distinction in agent files:

### ✅ Tools Available (Primary)
These are the tools the agent uses MOST OF THE TIME for their core responsibilities.

### 🔧 Tools Available When Needed (Secondary)
These are tools the agent CAN use when necessary, even if they're not used frequently.

### ❌ Tools Not in Scope
These represent capabilities the agent generally shouldn't focus on (e.g., "don't write production code" for architecture agents), but this is about FOCUS, not absolute prohibition.

## Example Scenarios

### Scenario 1: Architecture Agent Needs to Verify Structure

**Task**: Design a new module structure
**Primary approach**: Create architecture document using read/edit
**Can also do**: Use bash to verify current directory structure

```bash
ls -la src/        # Check existing structure
tree src/modules/  # Visualize module organization
```

**Why this is OK**: The agent needs accurate information about existing structure to design effectively.

### Scenario 2: Implementation Planner Verifies Dependencies

**Task**: Create implementation plan
**Primary approach**: Read code and create planning documents
**Can also do**: Check what dependencies are installed

```bash
pip list | grep pydantic  # Verify dependency version
```

**Why this is OK**: Accurate dependency information helps create better plans.

### Scenario 3: Issue Creation Agent Searches Duplicates

**Task**: Create a new issue
**Primary approach**: Use github-issues tool and search
**Can also do**: Use bash to search codebase for related patterns

```bash
grep -r "feature name" src/  # Find existing implementations
```

**Why this is OK**: More context helps avoid duplicate issues.

## Best Practices

### DO: Use the Right Tool for the Job
If bash helps you complete your task effectively, use it.

### DO: Follow Your Primary Focus
Architecture agents should focus on design, not implementation.

### DO: Use report_progress for Git
Always use report_progress for commits and PR operations.

### DON'T: Push Directly to Main
This is blocked by branch protection anyway.

### DON'T: Change Your Core Responsibility
Just because you CAN use all tools doesn't mean you SHOULD do work outside your domain.

## Summary

**Philosophy**: Trust agents to use appropriate tools to complete their work effectively.

**Primary tools** = What you use most often
**Available when needed** = What you can use if helpful
**Not in scope** = What's outside your core responsibility (but not strictly forbidden)

**Git operations**: All agents can create branches, commit, push to feature branches, and create PRs via report_progress. Branch protection (not agent restrictions) prevents direct pushes to main.

**Flexibility**: If a tool helps you complete your assigned task effectively, you can use it.
