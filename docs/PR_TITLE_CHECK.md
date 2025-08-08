# PR Title Check Workflow

This document describes the PR title validation workflow that ensures all pull requests follow conventional commit standards and include issue references.

## Workflow Details

**File**: `.github/workflows/pr-title-check.yml`
**Triggers**: Pull request events (opened, edited, synchronize)

## Validation Rules

### 1. Conventional Commit Format
PR titles must follow the conventional commit specification:

```
type(optional-scope): description
```

**Allowed Types:**
- `feat` - New features
- `fix` - Bug fixes
- `docs` - Documentation changes
- `style` - Code style changes
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Test additions/updates
- `chore` - Maintenance tasks

**Examples:**
- ✅ `feat: add new scanning feature`
- ✅ `fix(scanner): resolve timeout issue`
- ✅ `docs: update README`
- ❌ `Add new feature` (missing type)
- ❌ `FEAT: add feature` (uppercase type)

### 2. Issue Reference Requirement
PRs must reference an issue number either in the title or body:

**Examples:**
- ✅ `feat: add feature (#123)`
- ✅ Title: `feat: add feature` + Body contains: `Fixes #123`
- ❌ `feat: add feature` (no issue reference)

### 3. Subject Line Rules
- Must start with lowercase letter
- Should be descriptive and concise

## Workflow Jobs

### 1. Validate PR Title
Uses `amannn/action-semantic-pull-request@v5` to validate conventional commit format.

### 2. Validate Issue Reference
Uses `actions/github-script@v7` to check for issue number references (`#123` pattern).

## Handling Validation Failures

If the workflow fails:

1. **Check the error message** in the GitHub Actions log
2. **Update your PR title** to match the required format
3. **Ensure issue reference** is included in title or body
4. The workflow will re-run automatically when you update the PR

## Bypass Options

For special cases, PRs can be labeled with `ignore-semantic-pr` to bypass validation.

## Testing the Workflow

The workflow has been tested with these scenarios:

### Valid Titles
- `feat: add new feature (#123)`
- `fix: resolve scanner timeout (#456)`
- `docs: update installation guide (#789)`
- `refactor(cli): improve command structure (#111)`

### Invalid Titles
- `Add new feature` - Missing type
- `FEAT: add something` - Uppercase type
- `feat: Add feature` - Uppercase subject
- `feat: add feature` - Missing issue reference

## Troubleshooting

### Common Issues

1. **"Title doesn't match pattern"**
   - Ensure type is lowercase and from allowed list
   - Check for proper colon and space after type
   - Verify subject starts with lowercase

2. **"Missing issue reference"**
   - Add issue number to title: `feat: description (#123)`
   - Or reference in PR body: `Fixes #123`

3. **"Subject pattern error"**
   - Ensure subject line starts with lowercase letter
   - Example: `feat: add feature` not `feat: Add feature`