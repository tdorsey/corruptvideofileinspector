# Ralph with GitHub Copilot - Quick Start Guide

This guide explains how to use Ralph within GitHub Copilot for autonomous development without requiring external CLI tools.

## What is Ralph?

Ralph is an autonomous development tool that processes work items from a Product Requirements Document (prd.json) and implements them automatically. When integrated with GitHub Copilot, Ralph becomes a conversational AI assistant that helps you implement features systematically.

Ralph can work from multiple sources:
- **prd.json**: Local work item queue in `tools/ralph/config/prd.json`
- **GitHub Projects**: Track work items and status in GitHub Projects
- **GitHub Issues**: Individual issues that need implementation

## Quick Start (5 Minutes)

### Step 1: Check Available Work

Ralph can pull work from multiple sources:

**Option A: Local prd.json**
```bash
cat tools/ralph/config/prd.json
```

**Option B: GitHub Project**
```
@workspace Check GitHub Project 6 for Todo items and show me what needs to be done
```

**Option C: GitHub Issues**
```
@workspace List open issues labeled with 'feature' or specific component
```

### Step 2: Ask Copilot to Process a Work Item

Simply ask Copilot in your editor or chat:

**From prd.json:**
```
@workspace Read the next unprocessed work item from tools/ralph/config/prd.json 
and implement it following all the steps. Ensure all success criteria pass.
```

**From GitHub Project:**
```
@workspace Get the next Todo item from GitHub Project 6 and implement it. 
Update the project status to 'In Progress' when starting and 'Done' when complete.
```

**From GitHub Issue:**
```
@workspace Implement issue #236 following all requirements. Update status when complete.
```

### Step 3: Review and Commit

Copilot will:
- Show you what changes it's making
- Explain its approach
- Run tests if requested
- Commit with proper conventional commit messages
- **Update project/issue status** when complete

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

**From prd.json:**
```
@workspace Process the next work item from tools/ralph/config/prd.json
```

**From GitHub Project:**
```
@workspace Process the next Todo item from GitHub Project 6
```

**From GitHub Issues:**
```
@workspace Pick the highest priority open issue and implement it
```

### Process All Work Items

```
@workspace Process all Todo items from GitHub Project 6 one at a time. 
After each item:
1. Implement all requirements
2. Run tests
3. Commit with conventional commit message
4. Update project status to Done
5. Move to next item
```

### Check Progress

**Check prd.json:**
```
@workspace Show me which work items from tools/ralph/config/prd.json 
have been completed by checking git history and progress.txt
```

**Check GitHub Project:**
```
@workspace Show me the status of all items in GitHub Project 6
```

### Validate Work Item

```
@workspace Review the last work item I implemented. Check:
1. All steps were completed
2. All success criteria pass
3. Tests are passing
4. Code follows project standards
5. Project status updated (if applicable)
```

### Update Project Status

```
@workspace Update GitHub Project 6 item for issue #236 to status 'Done'
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
| GitHub Projects | Can query and update status | No integration |
| Work Sources | prd.json, Projects, Issues | prd.json only |

## Working with GitHub Projects

### Checking Project Status

Ralph can query GitHub Projects to see what needs to be done:

```
@workspace Show me all Todo items from GitHub Project 6
```

This is useful when:
- Multiple people are working on different items
- You want to prioritize based on project board
- Issues are tracked in GitHub Projects

### Updating Project Status

When Ralph completes a work item, it should update the project status:

**Manual update:**
```
@workspace Update GitHub Project 6 item for issue #236 to status 'Done'
```

**Automatic during implementation:**
```
@workspace Implement issue #236. When starting, update status to 'In Progress'. 
When complete and tests pass, update status to 'Done'.
```

### Project Field IDs

For the corruptvideofileinspector repository, Project 6 has:
- **Project ID**: `PVT_kwHOABKXZM4BMv4j`
- **Status Field ID**: `PVTSSF_lAHOABKXZM4BMv4jzg78XIM`
- **Status Options**:
  - Todo: `f75ad846`
  - In Progress: `47fc9ee4`
  - Done: `98236657`

Ralph can use these IDs to update project status programmatically.

### Example: Full Project Workflow

```
@workspace 
1. Check GitHub Project 6 for next Todo item
2. Implement that item following all requirements
3. Update status to 'In Progress' when starting
4. Run tests to verify implementation
5. Update status to 'Done' when complete
6. Create PR with conventional commit message
7. Move to next Todo item
```

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
