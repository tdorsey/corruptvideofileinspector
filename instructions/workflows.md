# GitHub Actions Workflow File Instructions

## Commit Message Guidelines
- **Commits to workflow files (`.github/workflows/*.yml`, `.github/workflows/*.yaml`) MUST NOT be marked as `fix:`.**
- Use `ci:` as the commit type for changes to workflow files.
- Example: `ci(workflow): update PR title validation script`
- This ensures that CI-related changes are tracked separately from bug fixes and feature changes.

## Best Practices
- Always validate workflow syntax before committing.
- Use marketplace actions when possible.
- Document any custom scripts or logic in workflow files.
- Reference related issues or PRs in commit messages when appropriate.
 - **Never use Python to test GitHub Actions workflow files.**
   - Use dedicated tools like `actionlint` or GitHub Actions itself for validation.
   - Do not create or maintain Python tests for `.github/workflows/*.yml` or `.yaml` files.

## Review and Approval
- All workflow changes should be reviewed by a maintainer familiar with CI/CD.
- Avoid making unrelated changes in workflow commits.

---
**Summary:**
- Use `ci:` for workflow file commits, not `fix:`.
- Validate and document all workflow changes.
- Seek review for CI/CD changes.
