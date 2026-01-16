---
applyTo: ".github/agents/**/*.agent.md"
---

# GitHub Copilot Agent Development Guidelines

When creating or modifying agent files in `.github/agents/`, follow these guidelines to ensure consistency and effectiveness.

## Agent File Structure

### YAML Frontmatter (Required)
```yaml
---
name: Agent Name
description: Brief description of agent's purpose and domain
tools:
  - read
  - edit
  - search
---
```

**Required Fields**:
- `name`: Human-readable agent name (can default to filename)
- `description`: One-line description of agent purpose and focus area
- `tools`: Array of allowed tools (`read`, `edit`, `search`, `comment`)

**Optional Fields**:
- `mcp-servers`: MCP servers to extend capabilities
- `model`: Specific AI model (IDE agents only)
- `target`: `vscode` or `github-copilot`

### Markdown Prompt Content

After front matter, include comprehensive prompt defining:
1. Agent's focus and responsibilities
2. What agent DOES (✅)
3. What agent does NOT do (❌)
4. Repository-specific context
5. Examples and best practices
6. Integration with other agents

## Agent Design Principles

### 1. Clear Focus Boundaries

**Good**: Specific, well-defined scope
```markdown
### ✅ What You DO
- Draft and create new issues
- Identify duplicate issues
- Structure issue metadata

### ❌ What You DON'T DO
- Implement features
- Write code or tests
```

**Bad**: Overlapping or vague responsibilities
```markdown
### What You DO
- Help with development tasks
- Fix issues
```

### 2. Repository-Specific Context

Include relevant project information:
- Project structure and key directories
- Technologies and frameworks used
- Coding standards and conventions
- Build/test commands
- Design patterns in use

### 3. Comprehensive Examples

Provide clear examples of:
- Good inputs/outputs for the agent
- Common scenarios and workflows
- Integration with other agents
- Handling edge cases

### 4. Size Limit

- **Maximum**: 30,000 characters per agent file
- Keep prompts concise but comprehensive
- Use examples sparingly but effectively

## SDLC Agent Types

This repository implements agents for each stage of software development:

1. **Issue Creation Agent** - Idea/Requirement stage
   - Drafts issues, identifies duplicates
   - Only creates/updates issues
   - Does NOT implement features

2. **Implementation Planner Agent** - Feature Planning stage
   - Breaks down requirements into tasks
   - Creates technical specifications
   - Does NOT write production code

3. **Architecture Designer Agent** - Architecture Design stage
   - Designs system architecture and data models
   - Creates diagrams and API designs
   - Does NOT implement code

4. **Lint Error Agent** - Lint/Static Analysis stage
   - Detects lint and style errors
   - Advisory only
   - Does NOT auto-fix without approval

5. **Feature Creator Agent** - Coding/Implementation stage
   - Writes production code
   - Implements planned features
   - Does NOT write tests

6. **Refactoring Agent** - Refactoring stage
   - Optimizes code structure
   - Behavior-preserving changes
   - Does NOT add features

7. **Test Agent** - Testing stage
   - Creates and fixes tests
   - Identifies failing tests
   - Does NOT write production code

8. **Code Reviewer Agent** - Code Review stage
   - Reviews PRs for quality
   - Advisory only
   - Does NOT merge PRs

9. **Security Reviewer Agent** - Security Review stage
   - Identifies vulnerabilities
   - Provides security guidance
   - Does NOT fix issues automatically

## Agent Integration Patterns

### Sequential Workflow
```
Issue Creation → Implementation Planner → Architecture Designer 
→ Feature Creator → Test Agent → Code Reviewer → Security Reviewer
```

### Parallel Support
```
Feature Creator ← Implementation Planner → Test Agent
                ↓
          Lint Error Agent
```

### Refactoring Flow
```
Code Reviewer → Refactoring Agent → Test Agent → Code Reviewer
```

## Testing Agent Files

### Validation Checklist
- [ ] YAML frontmatter is valid
- [ ] All required fields present
- [ ] Prompt under 30,000 characters
- [ ] Focus boundaries clearly defined
- [ ] No overlap with other agents
- [ ] Repository context included
- [ ] Examples provided
- [ ] Integration patterns documented

### Manual Testing
1. Invoke agent with sample task
2. Verify agent stays within scope
3. Check that agent refuses out-of-scope requests
4. Test integration with related agents

## Common Patterns

### Tool Access Levels

**Read-Only Agents** (Reviewers):
```yaml
tools:
  - read
  - search
```

**Advisory Agents** (Planners, Reviewers):
```yaml
tools:
  - read
  - edit  # For documentation only
  - search
```

**Implementation Agents** (Creators, Refactors):
```yaml
tools:
  - read
  - edit
  - search
```

### Scope Boundaries

Always clearly separate:
- **Planning vs Implementation**: Planners document, creators implement
- **Writing Code vs Writing Tests**: Feature creators vs test agents
- **Reviewing vs Fixing**: Reviewers advise, agents fix

### Repository Context Template

```markdown
## Repository Context

### Project Structure
```
src/
├── cli/          # Description
├── core/         # Description
└── config/       # Description
```

### Technologies
- Language: Python 3.13
- Framework: Typer CLI
- Testing: pytest
- Quality: Black + Ruff + MyPy

### Coding Standards
- Type annotations required
- Black formatting enforced
- 79-character line length
- Conventional commits required
```

## Examples of Good Agent Files

### Well-Scoped Agent
```markdown
# Issue Creation Agent

You are focused **ONLY** on creating and managing issues.

### ✅ What You DO
- Draft new issues with proper structure
- Identify duplicate issues
- Apply appropriate labels

### ❌ What You DON'T DO
- Implement features or write code
- Review or merge pull requests
- Run tests or builds
```

### Clear Repository Context
```markdown
## Repository: Corrupt Video Inspector

**Purpose**: Python CLI for detecting corrupted videos

**Key Modules**:
- `src/cli/`: Command handlers (Typer)
- `src/core/`: Business logic (scanner)
- `src/ffmpeg/`: FFmpeg integration

**Commands**:
- Build: `make build`
- Test: `make test`
- Lint: `make check`
```

## Anti-Patterns

### ❌ Vague Scope
```markdown
### What You DO
- Help with development
- Improve code quality
```

### ❌ Overlapping Responsibilities
```markdown
# Feature Agent
- Write production code
- Write tests  # <- Should be Test Agent
- Review code  # <- Should be Code Reviewer Agent
```

### ❌ Missing Context
```markdown
# Agent without repository context
Just write good code following best practices.
```

### ❌ No Examples
```markdown
Create issues properly.
# How? What format? What fields?
```

## Maintenance

### Updating Agents
- Keep agents aligned with repository changes
- Update context when project structure changes
- Refine scope based on usage patterns
- Add examples from actual usage

### Versioning
- Agent files are version controlled
- Document significant changes in commit messages
- Test after modifications
- Update related agents if integration changes

## Summary

Good agent files are:
- **Focused**: Clear, narrow scope with explicit boundaries
- **Contextual**: Include repository-specific information
- **Practical**: Provide actionable examples and patterns
- **Integrated**: Document relationships with other agents
- **Validated**: YAML valid, under character limit, tested

When creating agents, think about:
1. What is this agent's unique responsibility?
2. Where does it fit in the SDLC?
3. Which agents does it work with?
4. What repository context does it need?
