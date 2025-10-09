# PR Title Check Workflow

This document describes the enhanced PR title validation workflow that ensures all pull requests follow conventional commit standards, include issue references, and provides automated feedback and management.

## Workflow Details

**File**: `.github/workflows/pr-title-check.yml`
**Triggers**: Pull request events (opened, edited, synchronize)
**Permissions**: `contents: read`, `pull-requests: write`, `issues: read`

## Key Features

✨ **Automated PR Management**: Failed PRs are automatically converted to draft status
📝 **Detailed Feedback**: Clear comments explaining validation failures and how to fix them
🔔 **Assignee Notifications**: Automatic notifications to PR assignees when validation fails
✅ **Success Feedback**: Confirmatory comments when validation passes for draft PRs

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
PRs must reference an issue number in the title, body, or branch name:

**Examples:**
- ✅ **Title:** `feat: add feature (#123)`
- ✅ **Body:** `Fixes #123`, `Closes #456`, or `(#789)`
- ✅ **Branch:** `issue-123-description`, `fix-456-bug`, or `feature-789-new`
- ❌ `feat: add feature` (no issue reference anywhere)

**Detection Logic:**
- **Priority:** Title → Body → Branch Name
- **Patterns:** `#123` format in title/body, `issue-123-*` patterns in branch names
- **Enhanced:** Now includes comprehensive debugging and multiple detection methods

### 3. Subject Line Rules
- Must start with lowercase letter
- Should be descriptive and concise

## Workflow Jobs

### 1. Validate PR Title Format
Uses `amannn/action-semantic-pull-request@v5` marketplace action to validate conventional commit format.

### 2. Validate Issue Reference and Handle Failures
Uses `actions/github-script@v7` official GitHub action to:
- Check for issue number references (`#123` pattern)
- Handle validation failures by setting PR to draft
- Post detailed feedback comments
- Notify PR assignees

## Automated Response to Validation Failures

When validation fails, the workflow automatically:

1. **Converts PR to Draft**: The PR is automatically set to draft status
2. **Posts Detailed Comment**: A comprehensive comment explaining:
   - What validation rules failed
   - How to fix each issue
   - Examples of correct formats
3. **Notifies Assignees**: If the PR has assignees, they are mentioned in a follow-up comment
4. **Fails the Workflow**: The workflow fails to prevent merging until issues are resolved

### Example Failure Comment

```markdown
## 🚫 PR Validation Failed

This pull request has been automatically converted to **draft** due to validation failures.

### Issues Found:
❌ **PR title format validation failed**
   The PR title must follow conventional commit format: `type: description`
   Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
   Example: `feat: add new video validation feature`

❌ **Missing issue reference**
   PR must reference an issue number (e.g., #123) either in the title or body
   Example: `feat: add new feature (#123)` or add "Fixes #123" to PR body

### How to Fix:
1. **Fix the PR title format** if needed:
   - Use conventional commit format: `type: description`
   - Ensure description starts with lowercase letter
   - Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

2. **Add issue reference** if missing:
   - Include issue number in title: `feat: add feature (#123)`
   - Or add to PR body: `Fixes #123` or `Closes #123`

3. **Mark as ready for review** once all issues are resolved

---
*This check is automated. Once you fix the issues above, the validation will run again when you update the PR.*
```

## Success Response

When a draft PR passes validation, the workflow posts a success comment:

```markdown
## ✅ PR Validation Passed

All validation checks have passed! This PR is ready for review.

### Validated:
- ✅ PR title follows conventional commit format
- ✅ Issue reference found

You can now mark this PR as ready for review.
```

## Handling Validation Failures

If the workflow fails:

1. **Review the comment** posted on your PR for specific issues
2. **Fix your PR title** to match the required format
3. **Ensure issue reference** is included in title or body
4. **Update your PR** - the workflow will re-run automatically
5. **Mark as ready for review** once all validations pass

## Bypass Options

For special cases, PRs can be labeled with `ignore-semantic-pr` to bypass validation.

## Workflow Architecture

The refactored workflow follows these principles:
- **Marketplace Actions First**: Uses well-maintained marketplace actions (`amannn/action-semantic-pull-request@v5`, `actions/github-script@v7`)
- **Minimal Permissions**: Only requests necessary permissions for operation
- **User-Friendly Feedback**: Provides clear, actionable instructions
- **Automated Management**: Reduces manual intervention needed

## Testing Scenarios

### Valid PRs
- `feat: add new feature (#123)`
- `fix: resolve scanner timeout (#456)`
- `docs: update installation guide (#789)`
- `refactor(cli): improve command structure (#111)`

### Invalid PRs (will be set to draft)
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
   - Or reference in PR body: `Fixes #123`, `Closes #123`, `(#123)`
   - Or use descriptive branch name: `issue-123-description`
   - **Fixed in v2:** Enhanced detection now properly finds issue references in all locations

3. **"Subject pattern error"**
   - Ensure subject line starts with lowercase letter
   - Example: `feat: add feature` not `feat: Add feature`

4. **"PR was converted to draft"**
   - Check the validation comment for specific issues
   - Fix the issues mentioned
   - Update the PR to trigger re-validation
   - Mark as ready for review once validation passes

### Recent Fixes

**Issue #178 (Fixed):** PR workflow was failing to detect issue references in PR bodies
- **Problem:** References like `(#174)` at the end of PR body were not being detected
- **Solution:** Enhanced workflow logic with comprehensive debugging and multiple detection methods  
- **Improvement:** Added branch name detection and better error messages
- **Testing:** Added comprehensive test suite to prevent regression