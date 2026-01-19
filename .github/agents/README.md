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

## Related Documentation

- Main Copilot instructions: `..//copilot-instructions.md`
- Workflow automation: `../workflows/README.md`
- General instructions: `../instructions/`
