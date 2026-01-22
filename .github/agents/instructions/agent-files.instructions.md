---
applyTo: ".github/agents/*.md"
---

# Agent Instruction File Guidelines

When creating or modifying agent instruction files, follow these guidelines:

## File Naming Convention

Agent files must follow the naming pattern: `<agent-name>.agent.md`

Examples:
- `code-reviewer.agent.md`
- `feature-creator.agent.md`
- `issue-creation.agent.md`

## Required YAML Frontmatter

Every agent file MUST start with YAML frontmatter:

```yaml
---
name: Agent Name
description: Brief description of agent's purpose
tools:
  - read
  - edit
  - search
  - bash  # If agent needs to run commands
skills:
  - skill-name  # If agent uses a skill
---
```

## Required Sections

### 1. Title and Introduction
```markdown
# Agent Name

You are a specialized agent focused on **Primary Role** within the software development lifecycle.
```

### 2. Tool Authority Section (REQUIRED)
```markdown
## Tool Authority

### ✅ Tools Available

- **read** - Description of what read access is for
- **edit** - Description of what edit access is for
- **search** - Description of what search is for
- **bash** - Description of what bash commands are allowed (if applicable)

### ❌ Tools NOT Available

- **git commit/push** - Use report_progress tool instead
- **github API** - Don't interact with issues/PRs directly (unless agent has github-issues tool)

**Rationale**: Explain why this agent has/doesn't have specific tools.
```

### 3. Label Authority (If Applicable)
```markdown
## Label Authority

**You have specific label modification authority:**

✅ **Can Add:**
- `label:name` (when condition)

✅ **Can Remove:**
- `label:name` (when condition)

❌ **Cannot Touch:**
- Labels outside your domain
```

### 4. Your Focus Section
```markdown
## Your Focus

You **ONLY** handle [specific tasks]:

### ✅ What You DO

1. **Primary Responsibility**
   - Specific action 1
   - Specific action 2

### ❌ What You DON'T DO

- Things outside your scope
- Actions reserved for other agents
```

### 5. Best Practices and Examples

Include concrete examples of:
- How to perform agent tasks
- Common workflows
- Expected output formats
- Error handling

### 6. File Format Guidelines (If Relevant)

Include the standard file format selection guidelines for JSONL, YAML, and Markdown.

## Tool Specifications

### Agents That Should Have Bash
These agent types need bash for validation:
- Code reviewers (run `make check`, `make test`)
- Feature creators (run `make check`, `make format`)
- Test agents (run `pytest`, `make test`)
- Lint agents (run `make lint`, `make format`)
- Security reviewers (run `bandit`, `safety`)
- Refactoring agents (run tests to verify behavior)
- PR conflict resolution (run `git diff`, `make check`)

### Agents That Should NOT Have Bash
These agent types are documentation-focused:
- Architecture designers (design, don't execute)
- Implementation planners (plan, don't execute)

### Special Tool: github-issues
Only issue-related agents should have this tool:
```yaml
tools:
  - github-issues  # Create, read, update GitHub issues
  - read
  - edit
  - search
```

## Common Mistakes to Avoid

❌ Missing YAML frontmatter
❌ No Tool Authority section
❌ Unclear tool rationale
❌ Missing "What You DO" / "What You DON'T DO"
❌ Vague descriptions
❌ No concrete examples
❌ Wrong tools for agent type
❌ Conflicting responsibilities with other agents

## Agent Coordination

Document how your agent interacts with others:

```markdown
## Working with Other Agents

### Agent A → You
- **They provide**: Input or precondition
- **You create**: Output or result

### You → Agent B
- **You provide**: Output or result
- **They create**: Next step
```

## Commit Guidelines

When modifying agent files:
```bash
# Commit message format (agents are docs, not features)
docs(agents): <description>

# Examples
docs(agents): add tool authority section to code reviewer
docs(agents): update lint error agent with bash tool
docs(agents): clarify label permissions for security reviewer
```

## Validation Checklist

Before committing agent changes:
- [ ] YAML frontmatter is valid
- [ ] All tools are listed in frontmatter
- [ ] Tool Authority section present
- [ ] Rationale for tools provided
- [ ] Clear "DO" and "DON'T" sections
- [ ] Examples included
- [ ] No tool conflicts with other agents
- [ ] Agent name matches filename
- [ ] copilot.yml updated if new agent added

## Integration with copilot.yml

When creating a new agent, also update `.github/copilot.yml`:

```yaml
agents:
  available:
    - architecture-designer
    - code-reviewer
    - your-new-agent  # Add here
```

## Example Agent Structure

```markdown
---
name: Example Agent
description: Brief one-line description
tools:
  - read
  - edit
---

# Example Agent

Introduction paragraph.

## Tool Authority

### ✅ Tools Available
- Tool list with rationale

### ❌ Tools NOT Available
- What's not allowed

**Rationale**: Why these tools.

## Your Focus

### ✅ What You DO
1. Primary tasks

### ❌ What You DON'T DO
- Out of scope

## [Other sections...]

## Summary

Closing statement about agent's role.
```
