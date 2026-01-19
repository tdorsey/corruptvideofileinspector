---
applyTo: ".github/agents/**/*.agent.md"
---

# Label System for Agent Workflow Management

## Overview

This repository uses a prefix-based label system to manage workflow automation and agent permissions. Labels follow strict naming conventions to enable automated workflow transitions.

## Label Prefixes

### status:* (Workflow Stage)
Indicates where an issue/PR is in the development lifecycle.

- `status:draft` - Work in progress
- `status:in-triage` - Being evaluated
- `status:planning` - Architecture phase
- `status:in-development` - Active coding
- `status:in-review` - Under code review
- `status:security-review` - Security evaluation
- `status:merge-conflict` - Has conflicts
- `status:ready-to-merge` - Approved

### needs:* (Blocking Requirement)
Indicates what's preventing progress.

- `needs:architecture-design`
- `needs:implementation`
- `needs:tests`
- `needs:documentation`
- `needs:lint-fixes`
- `needs:code-review`
- `needs:security-review`
- `needs:conflict-resolution`
- `needs:maintainer-approval`
- `needs:changes`

### help:* (Author Needs Assistance)
Indicates author needs guidance.

- `help:conflict-resolution`
- `help:architecture`
- `help:testing`

## Agent Authority Matrix

Each agent has bounded authority over specific labels. **Agents must not modify labels outside their domain.**

| Agent | Can Add | Can Remove | Cannot Touch |
|-------|---------|------------|--------------|
| **Issue Creation Agent** | `needs:architecture-design` | `status:in-triage` | All other status/* |
| **Architecture Designer** | `needs:implementation`, `status:planning` | `needs:architecture-design` | Security/review labels |
| **Lint Error Agent** | `needs:lint-fixes` | `needs:lint-fixes` (when fixed) | All status/* labels |
| **Feature Creator** | `needs:tests`, `needs:documentation` | `needs:implementation` | Review status labels |
| **Test Agent** | `status:in-development` | `needs:tests` | Review status labels |
| **Code Reviewer** | `status:in-review`, `needs:changes`, `needs:code-review` | `status:draft`, `needs:code-review` | `status:security-review` |
| **Security Reviewer** | `status:security-review`, `needs:security-fixes` | `status:security-review` (when clean) | Merge labels |
| **Refactoring Agent** | `needs:code-review`, `needs:tests` | N/A (advisory only) | Status labels |

## Workflow Rules

### 1. Domain Boundaries
Agents only modify labels in their domain. Architecture agent cannot clear `needs:security-review`.

### 2. Status Progression
Issues/PRs must progress through appropriate stages:
```
in-triage → planning → in-development → in-review → [security-review] → ready-to-merge
```

### 3. Needs Clearance
Clearing all `needs:*` labels in a stage allows progression to next `status:*`.

### 4. Escalation
When encountering labels outside authority, agent should:
- Comment mentioning the blocking label
- Tag appropriate agent or maintainer
- Not attempt to modify the label

### 5. Conflict Detection
Code Review Agent must check for `status:merge-conflict` before marking work complete.

### 6. Draft Management
Code Review Agent removes `status:draft` only when:
- No merge conflicts
- All tests pass
- No `needs:*` labels remain
- Code review complete

## Example Workflow

```
1. Issue created
   → Add: status:in-triage

2. Triage Agent processes
   → Remove: status:in-triage
   → Add: needs:architecture-design

3. Architecture Agent designs
   → Remove: needs:architecture-design
   → Add: needs:implementation, status:planning

4. Feature Creator implements
   → Remove: needs:implementation
   → Add: needs:tests, needs:code-review, status:in-development

5. Test Agent adds tests
   → Remove: needs:tests

6. Code Reviewer reviews
   → Check: no needs:* labels remain
   → Check: no merge conflicts
   → Remove: status:draft, needs:code-review
   → Add: status:in-review (or status:ready-to-merge if no security concerns)

7. Security Reviewer (if needed)
   → Add: status:security-review
   → Review and remove when clean

8. Maintainer merges
   → Issue/PR closed
```

## Label Query Examples

Find all items needing implementation:
```
label:needs:implementation
```

Find all items in code review:
```
label:status:in-review
```

Find all merge-ready PRs:
```
label:status:ready-to-merge is:pr is:open
```

Find items with conflicts:
```
label:status:merge-conflict is:pr is:open
```

## Best Practices

1. **Always check label authority** before modifying
2. **Comment when blocked** by labels outside your domain
3. **Verify prerequisites** before removing blocking labels
4. **Update status** when transitioning workflow stages
5. **Escalate appropriately** when help is needed
6. **Never skip stages** in the workflow progression
7. **Document reasoning** when adding blocking labels

## Integration with Ralph

Ralph workflow checks status labels before marking items complete:
- `status:merge-conflict` = Work not complete
- `needs:*` labels present = Work not complete
- `status:ready-to-merge` = Work complete, update project status

This ensures accurate progress tracking and prevents premature completion.
