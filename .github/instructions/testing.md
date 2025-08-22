# ---
applyTo: "tests/**/*.py"
# ---
# Testing Instructions

## Testing Environment Setup

### Containerized Testing
1. **Use containerized testing environment**:
   ```bash
   docker-compose run --rm app python -m pytest
   ```
2. **Run existing tests**: Always run tests before making changes
3. **Environment validation**: Verify all required environment variables are documented and validated

## Test Writing Guidelines

### Test Structure
- Follow project's existing test patterns and organization
- Use descriptive test names that explain the behavior being tested
- Organize tests in logical groups (unit, integration, end-to-end)

### Test Quality Standards
- **Type Annotations**: Include type hints in test functions where applicable
- **Docstrings**: Document complex test scenarios
- **Assertions**: Use specific assertions that provide clear failure messages
- **Test Data**: Use fixtures for reusable test data
- **Mocking**: Mock external dependencies appropriately

### Test Categories
- **Unit Tests**: Test individual functions/methods in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows


### Linting and Formatting
- **Prefer running formatting tools (e.g., black, ruff) and allowing them to auto-fix lint errors, rather than manually rewriting or sorting entire files.**
- Automated tools ensure consistency and reduce the risk of introducing errors during manual changes.

### Required Testing Practices

**CRITICAL: Do NOT create Python tests for GitHub Actions workflows**:
- NEVER write Python code to test `.github/workflows/*.yml` or `.yaml` files
- Workflow files should be validated using `actionlint` or GitHub Actions itself
- Python tests for workflows create unnecessary maintenance overhead

Standard Testing Practices:
1. **Test before changes**: Always run `make test` before making changes to validate existing functionality
2. **Test after changes**: Run `make test` after changes to ensure nothing is broken
3. **Integration with quality checks**: Use `make check` which includes testing as part of the full validation
4. **Test Coverage**: Maintain appropriate test coverage for new code
5. **Test Isolation**: Ensure tests don't depend on each other
6. **Cleanup**: Properly clean up test resources (temp files, database records, etc.)
7. **Error Cases**: Test both success and failure scenarios
8. **Edge Cases**: Test boundary conditions and edge cases

## Development Testing Workflow

### Pre-Development Testing
```bash
# Always validate current state before making changes
make test
```

### Post-Development Testing
```bash
# Validate your changes
make test

# Run full quality check including tests
make check
```

### Testing Integration with Development Flow
1. **Before changes**: `make test` to ensure baseline functionality
2. **During development**: Run focused tests as needed
3. **Before commit**: `make check` (includes `make test` plus format/lint/type)
4. **Pull request**: All tests must pass - no exceptions

## Test Configuration

### Test Environment Variables
- Use separate configuration for testing environments
- Document test-specific environment variables
- Ensure tests work with minimal configuration

### Test Dependencies
- Keep test dependencies separate from production dependencies
- Use appropriate test frameworks (pytest, unittest, etc.)
- Configure test runners properly in pyproject.toml

## Debugging Tests

### Common Issues
- Environment variable conflicts
- Test isolation problems
- Resource cleanup issues
- Timing-dependent test failures

### Debugging Techniques
- Use verbose test output (`-v` flag)
- Run individual tests for focused debugging
- Use test fixtures for consistent test environments
- Log test execution details when needed
