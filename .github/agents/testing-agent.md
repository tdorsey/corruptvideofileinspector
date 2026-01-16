---
name: testing-agent
description: Automates test generation and analysis for the Corrupt Video File Inspector project
model: claude-3-5-haiku-20241022
tools:
  - bash
  - grep
  - view
  - edit
  - create
skills:
  - testing
---

# Testing Agent

This agent assists with test generation, test analysis, and test quality improvements for the project.

## Related Skill

This agent uses the **Testing Skill** (`.github/skills/testing/SKILL.md`) which provides detailed documentation on:
- Test structure and organization
- Pytest conventions and markers
- Test fixture patterns
- Mocking strategies
- Coverage requirements

## Model Selection

Uses **Claude 3.5 Haiku** (claude-3-5-haiku-20241022) for cost-effective, frequent test generation and analysis tasks.

## Capabilities

### Test Generation
- Generate unit tests for new functions
- Create integration tests for workflows
- Generate parametrized tests for edge cases
- Create test fixtures and mock objects

### Test Analysis
- Analyze test coverage reports
- Identify untested code paths
- Suggest missing test scenarios
- Detect flaky or brittle tests

### Test Quality
- Review test structure and organization
- Ensure proper pytest marker usage
- Validate test isolation
- Check mock usage patterns

### Test Execution
- Run targeted test suites
- Execute tests with coverage analysis
- Debug failing tests
- Generate test reports

## When to Use

- When adding new functionality that needs tests
- When analyzing test coverage gaps
- When debugging failing tests
- When improving test quality and maintainability
- When setting up test fixtures or mocks

## Test Requirements

### Mandatory for All New Code
- Unit tests with `@pytest.mark.unit` marker
- Test coverage >80% for new functions
- Tests must be isolated and repeatable
- Tests must run in <5 seconds (unit tests)

### Test Organization
```
tests/
├── unit/              # Fast, isolated tests
├── integration/       # Component integration tests
└── fixtures/          # Shared test data and fixtures
```

## Instructions

### Test Generation Process

1. **Analyze Function**: Understand inputs, outputs, side effects
2. **Identify Scenarios**: Normal case, edge cases, error cases
3. **Create Test Cases**: One test per scenario
4. **Add Fixtures**: Create reusable test data
5. **Add Mocks**: Mock external dependencies (FFmpeg, API calls)

### Test Naming Convention

```python
def test_<function_name>_<scenario>() -> None:
    """Test description."""
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...
```

### Common Test Patterns

**Unit Test Template**
```python
import pytest
from pathlib import Path
from src.module import function_to_test

@pytest.mark.unit
def test_function_to_test_success_case() -> None:
    """Test successful execution of function_to_test."""
    # Arrange
    input_data = prepare_input()
    expected_result = calculate_expected()
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_result
```

**Parametrized Test Template**
```python
@pytest.mark.unit
@pytest.mark.parametrize("input_val,expected", [
    ("valid", True),
    ("invalid", False),
    ("", False),
])
def test_validation_multiple_inputs(
    input_val: str, expected: bool
) -> None:
    """Test validation with various inputs."""
    result = validate(input_val)
    assert result == expected
```

### Priority Areas

1. **New Functions**: Always generate tests for new code
2. **Bug Fixes**: Add regression tests
3. **Edge Cases**: Test boundary conditions
4. **Error Handling**: Test exception paths
5. **Integration Points**: Test component interactions

### Quality Checks

- Tests should be deterministic (no flakiness)
- Tests should be fast (<5 seconds for unit tests)
- Tests should be isolated (no dependencies)
- Tests should be readable (clear arrange/act/assert)
- Tests should use proper assertions (no bare asserts)
