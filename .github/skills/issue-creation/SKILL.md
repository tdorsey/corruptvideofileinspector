---
name: issue-creation
description: Skill for creating and triaging issues in the Corrupt Video File Inspector project
---

# Issue Creation Skill

This skill provides capabilities for creating, triaging, and formatting issues in the Corrupt Video File Inspector project.

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
