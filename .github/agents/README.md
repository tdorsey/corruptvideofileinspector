# Agent System Organization

This directory contains the agent system configuration for the Corrupt Video File Inspector project.

## Structure

### `personas/`
Agent persona definitions that specify agent behavior, capabilities, and responsibilities.
- Each persona file follows the `{name}.agent.md` naming convention
- Contains tool authority, scope, responsibilities, and boundaries
- Links to related skills and instructions

### `skills/`
Reusable skill definitions that agents can use to accomplish tasks.
- Each skill is in its own subdirectory with a `SKILL.md` file
- Contains procedural knowledge and best practices
- Independent of specific agent personas

### `instructions/`
General instructions and guidance for agents.
- Cross-cutting concerns and philosophies
- Guidelines for tool usage and decision-making
- Best practices for agent behavior

## Available Agent Personas

- **architecture-designer.agent.md** - Design system architecture and component interactions
- **code-reviewer.agent.md** - Review code for quality, correctness, and standards
- **feature-creator.agent.md** - Implement new features and enhancements
- **github-actions-troubleshooter.agent.md** - Debug and fix GitHub Actions workflows
- **implementation-planner.agent.md** - Plan implementation strategies
- **issue-creation.agent.md** - Create and triage issues
- **lint-error.agent.md** - Fix linting and formatting errors
- **pr-conflict-resolution.agent.md** - Resolve pull request merge conflicts
- **refactoring.agent.md** - Refactor code for maintainability
- **security-reviewer.agent.md** - Review code for security issues
- **test.agent.md** - Create and maintain tests

## Available Skills

- **issue-creation** - Creating, triaging, and formatting issues
- **pr-conflict-resolution** - Resolving merge conflicts in pull requests

## Agent Capabilities Matrix

| Agent | Primary Task | Tools | Runs Tests | Creates PRs | Example Use |
|-------|-------------|-------|-----------|-------------|-------------|
| architecture-designer | Design system architecture | read, edit, search | ❌ | ✅ | "Design database schema for feature X" |
| code-reviewer | Review code quality | read, search, bash | ✅ | ❌ | "Review PR #123 for code quality" |
| feature-creator | Build new features | read, edit, bash | ✅ | ✅ | "Implement video export feature" |
| github-actions-troubleshooter | Debug CI workflows | read, search, bash | ✅ | ✅ | "Fix failing release workflow" |
| implementation-planner | Create implementation plans | read, edit, search | ❌ | ✅ | "Plan implementation for issue #45" |
| issue-creation | Create and triage issues | read, edit, github-issues | ❌ | ❌ | "Triage Quick Capture issue" |
| lint-error | Fix code quality issues | read, edit, bash | ✅ | ✅ | "Fix all ruff and mypy errors" |
| pr-conflict-resolution | Resolve merge conflicts | read, edit, bash | ✅ | ✅ | "Resolve conflicts in PR #67" |
| refactoring | Improve code structure | read, edit, bash | ✅ | ✅ | "Refactor scanner module" |
| security-reviewer | Security code review | read, search, bash | ✅ | ❌ | "Security audit of auth module" |
| test | Create and fix tests | read, edit, bash | ✅ | ✅ | "Add tests for database service" |

## Agent Workflows

### Feature Development Flow
1. **@implementation-planner** - Create implementation plan with tasks and milestones
2. **@feature-creator** - Implement the feature following the plan
3. **@test** - Add comprehensive unit and integration tests
4. **@code-reviewer** - Review implementation for quality and standards
5. **@security-reviewer** - Security audit if handling sensitive data

### Bug Fix Flow
1. **@code-reviewer** - Analyze the bug and identify root cause
2. **@feature-creator** - Implement the fix with minimal changes
3. **@test** - Add regression tests to prevent recurrence
4. **@lint-error** - Fix any style issues introduced

### CI Failure Flow
1. **@github-actions-troubleshooter** - Diagnose workflow failure
2. **@lint-error** - Fix code quality issues (if applicable)
3. **@test** - Fix failing tests (if applicable)
4. **@code-reviewer** - Validate the fix

### Refactoring Flow
1. **@architecture-designer** - Design improved structure
2. **@refactoring** - Refactor code incrementally  
3. **@test** - Ensure tests still pass, add new tests if needed
4. **@code-reviewer** - Verify behavior preservation

## Related Documentation

- Main Copilot instructions: `..//copilot-instructions.md`
- Workflow automation: `../workflows/README.md`
- General instructions: `../instructions/`
