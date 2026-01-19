# Ralph with GitHub Copilot - Quick Start Guide

This guide explains how to use Ralph within GitHub Copilot for autonomous development without requiring external CLI tools.

## What is Ralph?

Ralph is an autonomous development tool that processes work items from a Product Requirements Document (prd.json) and implements them automatically. When integrated with GitHub Copilot, Ralph becomes a conversational AI assistant that helps you implement features systematically.

## Quick Start (5 Minutes)

### Step 1: Review Example Work Items

The repository includes example work items at `tools/ralph/config/prd.json`:

```bash
cat tools/ralph/config/prd.json
```

### Step 2: Ask Copilot to Process a Work Item

Simply ask Copilot in your editor or chat:

```
@workspace Read the next unprocessed work item from tools/ralph/config/prd.json 
and implement it following all the steps. Ensure all success criteria pass.
```

### Step 3: Review and Commit

Copilot will:
- Show you what changes it's making
- Explain its approach
- Run tests if requested
- Commit with proper conventional commit messages

That's it! You're using Ralph through Copilot.

## Creating Your Own Work Items

### Work Item Structure

Edit `tools/ralph/config/prd.json` with this structure:

```json
[
  {
    "category": "Feature Name",
    "description": "Detailed description of what needs to be implemented",
    "steps": [
      "Step 1: First action to take",
      "Step 2: Second action to take",
      "Step 3: Third action to take"
    ],
    "passes": [
      "Criterion 1: How to verify success",
      "Criterion 2: Another success criterion",
      "Criterion 3: Final validation check"
    ]
  }
]
```

### Real-World Example

```json
{
  "category": "Add Input Validation",
  "description": "Implement comprehensive input validation for video file paths to prevent processing invalid or dangerous file paths",
  "steps": [
    "Create validation functions in src/core/validators.py",
    "Add checks for: file existence, file type, path traversal attacks, symbolic links",
    "Implement clear error messages for each validation failure",
    "Add unit tests for all validation scenarios",
    "Integrate validation into video scanner entry point"
  ],
  "passes": [
    "All dangerous path patterns are rejected with clear errors",
    "Valid video files pass validation",
    "Unit tests achieve 100% coverage of validation logic",
    "Integration tests verify validation at scanner entry point",
    "Error messages guide users to fix their inputs"
  ]
}
```

## Common Copilot Commands

### Process Next Work Item

```
@workspace Process the next work item from tools/ralph/config/prd.json
```

### Process All Work Items

```
@workspace Process all unfinished work items from tools/ralph/config/prd.json 
one at a time. After each work item, run tests and commit if passing.
```

### Check Progress

```
@workspace Show me which work items from tools/ralph/config/prd.json 
have been completed by checking git history and progress.txt
```

### Validate Work Item

```
@workspace Review the last work item I implemented. Check:
1. All steps were completed
2. All success criteria pass
3. Tests are passing
4. Code follows project standards
```

## Advantages Over CLI Mode

| Feature | Copilot Mode | CLI Mode |
|---------|--------------|----------|
| Setup Required | None | Install Copilot CLI, authenticate |
| Interaction | Interactive, conversational | Batch, automated |
| Context | Full codebase awareness | Limited to prompts |
| Flexibility | Easy to adjust mid-implementation | Fixed automation |
| Feedback | Real-time, explanatory | Post-iteration only |
| Learning Curve | Minimal - natural language | Moderate - config files |

## Best Practices

### 1. Start Small

Begin with simple, well-defined work items:
- Single file changes
- Clear success criteria
- No complex dependencies

### 2. Be Specific in Steps

Good:
```json
"steps": [
  "Create src/utils/validator.py with validate_path() function",
  "Add checks for: exists, is_file, has_video_extension",
  "Write unit tests in tests/unit/test_validator.py",
  "Import and use in src/core/scanner.py line 45"
]
```

Bad:
```json
"steps": [
  "Add validation",
  "Make it work",
  "Test it"
]
```

### 3. Include Verification Steps

Always include in your `passes`:
- Unit test requirements
- Integration test scenarios
- Code quality checks (linting, type checking)
- Specific behavior validations

### 4. Review Before Committing

Even though Copilot can commit automatically:
- Review the changes carefully
- Run full test suite: `make test`
- Check code quality: `make check`
- Validate manually if needed

### 5. Use Conventional Commits

Ensure work item categories map to conventional commit types:
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation
- `test`: Test improvements
- `refactor`: Code restructuring
- `chore`: Maintenance tasks

## Troubleshooting

### "I don't have tools/ralph/config/prd.json"

Create it:
```bash
mkdir -p tools/ralph/config
cat > tools/ralph/config/prd.json << 'EOF'
[
  {
    "category": "Test Work Item",
    "description": "Verify Ralph integration works by adding a simple utility function",
    "steps": [
      "Create src/utils/greeting.py with hello() function that returns 'Hello, Ralph!'",
      "Add unit test in tests/unit/test_greeting.py",
      "Ensure test passes"
    ],
    "passes": [
      "Function returns expected string",
      "Unit test passes",
      "Code is type-hinted and follows project standards"
    ]
  }
]
EOF
```

### "Copilot isn't following the steps"

Be more explicit:
```
@workspace Implement the work item from tools/ralph/config/prd.json.

Requirements:
- Follow EACH step exactly in order
- After each step, verify it's complete before moving to next
- Show me the changes after each step
- Don't skip any steps
```

### "How do I track progress?"

Create `tools/ralph/progress.txt` or ask:
```
@workspace Update tools/ralph/progress.txt with:
- Today's date
- Work item category completed
- Brief summary of changes
- Commit SHA
```

### "Can I use this with the traditional CLI mode?"

Yes! The work items in `prd.json` work with both:
- **Copilot mode**: Interactive, conversational
- **CLI mode**: Automated, batch processing via `nx run ralph:once`

Choose based on your workflow preferences.

## Example Session

Here's a complete example session using Ralph with Copilot:

```
You: @workspace Show me the work items in tools/ralph/config/prd.json

Copilot: I found 3 work items:
1. Add Input Validation (Status: Not started)
2. Improve Error Messages (Status: Not started)  
3. Add Integration Tests (Status: Not started)

You: Process the first work item

Copilot: I'll implement "Add Input Validation". Let me start with step 1...

[Copilot creates src/core/validators.py]

Copilot: Created validators.py with path validation. Moving to step 2...

[Continues through all steps]

Copilot: All steps complete. Running tests...
Tests passed! All success criteria met:
✓ Dangerous paths rejected
✓ Valid files pass validation
✓ 100% test coverage
✓ Integration tests pass

Ready to commit. Suggested message:
"feat(core): add input validation for video file paths"

You: Looks good, commit it

Copilot: Committed as 3f8a9c1
```

## Advanced Usage

### Conditional Work Items

Create work items that depend on previous ones:

```json
{
  "category": "Add Feature Y",
  "description": "Implement feature Y (requires Feature X from previous work item)",
  "steps": [
    "Verify Feature X exists (src/features/x.py)",
    "Import and extend Feature X...",
    "..."
  ]
}
```

### Multi-Phase Work Items

Break complex features into phases:

```json
[
  {
    "category": "Cache System - Phase 1: Basic Cache",
    "description": "Implement basic in-memory cache",
    "steps": ["..."]
  },
  {
    "category": "Cache System - Phase 2: Persistence",
    "description": "Add disk persistence to cache",
    "steps": ["..."]
  },
  {
    "category": "Cache System - Phase 3: Expiration",
    "description": "Add cache expiration and cleanup",
    "steps": ["..."]
  }
]
```

### Testing-Focused Work Items

Create work items specifically for testing:

```json
{
  "category": "Improve Test Coverage for Scanner",
  "description": "Increase scanner.py test coverage from 75% to 95%",
  "steps": [
    "Run coverage report: pytest tests/ --cov=src/core/scanner --cov-report=term-missing",
    "Identify untested code paths in scanner.py",
    "Write unit tests for each untested path",
    "Verify coverage reaches 95%"
  ],
  "passes": [
    "Coverage report shows >= 95% for scanner.py",
    "All new tests pass",
    "No existing tests broken"
  ]
}
```

## Tips for Writing Great Work Items

### 1. Single Responsibility
Each work item should implement ONE feature or fix ONE issue.

### 2. Testable
Always include test requirements in steps and success criteria.

### 3. Specific File References
Reference specific files and line numbers when possible:
```
"Update src/core/scanner.py line 123 to use new validator"
```

### 4. Clear Success Criteria
Make success criteria objective and verifiable:
- ✅ "All unit tests in tests/unit/test_cache.py pass"
- ❌ "Cache works correctly"

### 5. Consider Edge Cases
Include edge case handling in steps:
```
"Add error handling for: empty files, corrupted files, permission denied, disk full"
```

## Related Documentation

- [Ralph README](README.md) - Full Ralph documentation
- [Ralph Setup](SETUP.md) - Traditional CLI setup
- [Product Requirements Document](config/prd.json) - Example work items
- [GitHub Copilot Documentation](https://docs.github.com/copilot)

## Getting Help

### In Copilot Chat

```
@workspace Help me write a work item for [your feature description]
```

Copilot will help you structure a proper work item.

### Common Issues

Ask Copilot:
```
@workspace The work item didn't work as expected. Debug issues with:
1. Check if all files were created
2. Verify tests pass
3. Check for import errors
4. Review commit history
```

## Summary

Using Ralph with GitHub Copilot is as simple as:

1. **Create** work items in `tools/ralph/config/prd.json`
2. **Ask** Copilot to process them: `@workspace Process work item...`
3. **Review** changes and commit
4. **Repeat** for next work item

No installation, no configuration, just natural language interaction with your AI development assistant.

Happy coding! 🚀
