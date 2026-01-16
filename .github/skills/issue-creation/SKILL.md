---
name: issue-creation
description: Skill for creating and triaging issues in the Corrupt Video File Inspector project
---

# Issue Creation Skill

This skill provides capabilities for creating, triaging, and formatting issues in the Corrupt Video File Inspector project.

## Required Tools

### Allowed Tools

**Issue Management (REQUIRED)**
- GitHub Issues API - Create, update, and label issues
- GitHub CLI (`gh`) - Issue operations via command line
- `grep` / `view` - Inspect issue templates

**Text Processing (RECOMMENDED)**
- `jq` - JSON processing for API responses
- Standard text tools (`sed`, `awk`) - Issue formatting

**What to Use:**
```bash
# ✅ DO: Use GitHub CLI for issue operations
gh issue create --title "bug: video scan fails" --body "..."
gh issue list --label "bug" --state "open"
gh issue view 123

# ✅ DO: Use GitHub API for programmatic access
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/issues

# ✅ DO: Follow issue templates
ls .github/ISSUE_TEMPLATE/
cat .github/ISSUE_TEMPLATE/bug_report.yml
```

**What NOT to Use:**
```bash
# ❌ DON'T: Create issues without templates
# Always use provided templates

# ❌ DON'T: Use external issue tracking
jira                        # Use GitHub Issues
trello                      # Use GitHub Projects
asana                       # Use GitHub Issues

# ❌ DON'T: Bypass issue validation
# Don't skip required fields or labels
```

### Tool Usage Examples

**Example 1: Create Bug Report**
```bash
# Using GitHub CLI
gh issue create \
  --title "[FIX]: scanner crashes on MKV files" \
  --body "$(cat <<EOF
### Stakeholder Type
End User

### Component/Domain
Scanner

### I want to
Scan MKV video files without crashes

### But
The scanner crashes when processing MKV files

### Steps to Reproduce
1. Run: corrupt-video-inspector scan /videos
2. Scanner crashes on first MKV file

### Environment
- OS: Ubuntu 22.04
- Python: 3.13
- FFmpeg: 4.4.2
EOF
)" \
  --label "bug" \
  --label "component:scanner"
```

**Example 2: Triage Issue**
```bash
# Add labels based on content
gh issue edit 123 --add-label "priority:high"
gh issue edit 123 --add-label "component:cli"

# Move through triage workflow
gh issue edit 123 --remove-label "triage:agent-pending"
gh issue edit 123 --add-label "triage:agent-processed"
```

**Example 3: Classify Issue Type**
```python
# Issue classification logic
def classify_issue(issue_body: str) -> str:
    """Classify issue based on keywords."""
    content = issue_body.lower()
    
    bug_keywords = ['bug', 'error', 'crash', 'fail']
    feature_keywords = ['feature', 'enhancement', 'add']
    
    if any(kw in content for kw in bug_keywords):
        return 'bug'
    elif any(kw in content for kw in feature_keywords):
        return 'feature'
    return 'task'
```

**Example 4: Format Issue Body**
```python
# Format issue to match template
def format_bug_report(original_body: str) -> str:
    """Format bug report to template."""
    return f"""### Stakeholder Type
End User

### Component/Domain
Scanner

### I want to
{extract_goal(original_body)}

### But
{extract_problem(original_body)}

### Steps to Reproduce
{extract_steps(original_body)}

### Environment Information
{extract_environment(original_body)}
"""
```

## When to Use

Use this skill when:
- Creating a new issue for the project
- Triaging an unstructured issue submission
- Reformatting an existing issue to match project templates
- Analyzing issue content to determine appropriate labels and categories

## Available Issue Types

### Bug Report (`[FIX]:` prefix)
For reporting bugs or issues with the application.

**Required sections:**
- Stakeholder Type
- Component/Domain
- I want to (expected behavior)
- But (actual problem)
- This helps by (impact of fix)
- Unlike (contrast with expected)
- Steps to Reproduce
- Environment Information
- Error Logs/Output

### Feature Request (`[FEAT]:` prefix)
For proposing new features or enhancements.

**Required sections:**
- Stakeholder Type
- Component/Domain
- I want to (desired feature)
- But (current limitation)
- This helps by (benefit)
- Unlike (alternatives)
- Additional Context

### Chore/Maintenance (`[CHORE]:` prefix)
For maintenance tasks, dependency updates, or project improvements.

**Required sections:**
- Stakeholder Type
- Component/Domain
- I want to (task description)
- But (current issue)
- This helps by (benefit)
- Unlike (current state)
- Maintenance Task Type
- Specific Tasks

### Documentation (`[DOCS]:` prefix)
For documentation updates or improvements.

**Required sections:**
- Stakeholder Type
- Component/Domain (Documentation)
- I want to (documentation change)
- But (current state)
- This helps by (improvement)
- Unlike (current documentation)

### Quick Capture (`[QUICK]:` prefix)
For unstructured input that will be automatically triaged.

**Required sections:**
- Summary
- Additional Details (optional)

## Component/Domain Options

- CLI
- Scanner
- Trakt Integration
- Config
- Reporter
- Output
- Docker
- CI/CD
- GitHub Actions
- Tests
- Documentation
- Other

## Stakeholder Types

- Project Maintainer
- Contributor
- End User

## Classification Keywords

When analyzing issue content, use these keywords to determine the appropriate category:

### Bug Indicators
`bug`, `error`, `crash`, `fail`, `broken`, `issue`, `problem`, `not working`, `exception`, `traceback`

### Feature Indicators
`feature`, `enhancement`, `request`, `add`, `improve`, `want`, `would be nice`, `suggestion`, `propose`

### Documentation Indicators
`documentation`, `docs`, `readme`, `typo`, `clarify`, `explain`

### Performance Indicators
`performance`, `slow`, `fast`, `optimize`, `speed`, `memory`

## Automated Triage Process

1. User submits issue via Quick Capture template
2. Issue receives `triage:agent-pending` label
3. Issue Triage Agent workflow triggers
4. Original content is preserved as a comment
5. Issue is classified based on keywords
6. Issue body is reformatted to match appropriate template
7. Metadata comment is posted with:
   - Classification type
   - Confidence percentage
   - Gap analysis (missing information)
8. Labels are updated:
   - `triage:agent-pending` removed
   - `triage:agent-processed` added
   - Type-specific label added (bug, feature, etc.)

## Example Usage

### Creating a Bug Report

```markdown
### Stakeholder Type

End User

### Component/Domain

CLI

### I want to

Scan a directory of video files and get a report of corrupted files.

### But

The application crashes when encountering a specific video codec.

### This helps by

Allowing users to reliably scan all video formats.

### Unlike

The current behavior which causes the scan to fail completely.

### Steps to Reproduce

1. Create a directory with MKV files using VP9 codec
2. Run `corrupt-video-inspector scan /path/to/videos`
3. Application crashes with segmentation fault

### Environment Information

- OS: Ubuntu 22.04
- Python version: 3.13.0
- Application version: 2.0.0

### Error Logs/Output

```
Segmentation fault (core dumped)
```
```

### Creating a Feature Request

```markdown
### Stakeholder Type

Contributor

### Component/Domain

Scanner

### I want to

Add support for parallel video scanning to improve performance.

### But

Currently, videos are scanned sequentially which is slow for large libraries.

### This helps by

Reducing scan time by utilizing multiple CPU cores.

### Unlike

The current sequential scanning approach.

### Additional Context

Consider using Python's multiprocessing module with a configurable worker pool.
```
