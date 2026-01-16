---
name: general-coding-agent
description: General-purpose coding agent for the Corrupt Video File Inspector project
---

# Corrupt Video File Inspector - Agent Configuration

This file defines the capabilities, boundaries, and guidelines for GitHub Copilot agents working on this project.

## Agent Capabilities

### Code Development
- **Python Development**: Write Python 3.13 code with strict type checking
- **CLI Implementation**: Create Typer-based CLI commands and handlers
- **FFmpeg Integration**: Implement video processing using FFmpeg
- **Configuration Management**: Build Pydantic configuration models
- **Testing**: Write unit and integration tests with pytest

### Code Quality
- **Formatting**: Apply Black formatting (100 char line length)
- **Linting**: Apply Ruff linting rules
- **Type Checking**: Ensure MyPy compliance with strict mode
- **Testing**: Run pytest with appropriate markers

### Documentation
- **Code Comments**: Add docstrings for public APIs
- **Type Annotations**: Include comprehensive type hints
- **README Updates**: Update documentation as needed
- **Instruction Updates**: Keep instruction files current

## Agent Boundaries

### Allowed Actions
✅ **You CAN:**
- Read and modify files in the repository
- Run git commands to inspect repository state
- Execute make commands for building and testing
- Use report_progress tool to commit and push changes
- Install Python packages via pip/poetry (with network)
- Run tests and validation commands
- Create new files and directories
- Delete temporary files

### Prohibited Actions
❌ **You CANNOT:**
- Commit or push directly using git/gh commands (use report_progress instead)
- Update issues, PRs, or labels directly (no GitHub API access)
- Pull branches from GitHub (can only work with local state)
- Force push or rewrite history
- Access files in .github/agents directory (except this file)
- Clone other repositories
- Use git reset --hard or git rebase (force push unavailable)

## Development Standards

### Code Style Conventions
```python
# Type annotations on all public functions
def process_video(path: str, mode: str = "quick") -> Dict[str, Any]:
    """Process a video file for corruption detection.
    
    Args:
        path: Path to video file
        mode: Scan mode (quick, deep, hybrid)
        
    Returns:
        Dictionary with scan results
    """
    pass

# Use f-strings for formatting
message = f"Processing {filename} in {mode} mode"

# Follow Black formatting (100 char line length)
# Use descriptive variable names
# Import organization: stdlib, third-party, local
```

### Testing Requirements
```python
import pytest

# Mark unit tests
@pytest.mark.unit
def test_video_scanner_initialization():
    scanner = VideoScanner()
    assert scanner is not None

# Use descriptive test names
def test_quick_scan_detects_corrupted_video():
    result = quick_scan("corrupted.mp4")
    assert result.is_corrupted is True
```

### Commit Standards
- **MUST use Conventional Commits format**:
  - `feat(component): add new feature`
  - `fix(component): resolve bug`
  - `docs(component): update documentation`
  - `test(component): add tests`
  - `chore(component): maintenance task`
- **Description in lowercase** after type and scope
- **Atomic commits**: One logical change per commit

## Test Commands

### Pre-commit Validation
```bash
# MUST pass before every commit
make check                  # Runs black, ruff, mypy

# Run tests
make test                   # All tests
pytest tests/ -v -m "unit"  # Unit tests only
```

### Build Commands
```bash
make docker-build          # Build production image
make dev-build             # Build development image
```

### Environment Setup
```bash
export PYTHONPATH=src      # Enable imports without installation
make docker-env            # Generate Docker environment files
make secrets-init          # Create Trakt secret files
```

## Acceptance Criteria

### Definition of Done
A task is complete when:
- [ ] Code follows project conventions and style
- [ ] `make check` passes (formatting, linting, type checking)
- [ ] Tests pass (unit tests minimum, integration if applicable)
- [ ] Documentation updated (if public API changed)
- [ ] Changes committed using report_progress tool
- [ ] Manual validation performed for CLI changes

### Code Review Checklist
Before considering work complete:
- [ ] Type annotations on all public functions
- [ ] No hardcoded secrets or sensitive data
- [ ] Error handling for expected failure cases
- [ ] Tests cover new functionality
- [ ] Docstrings on public APIs
- [ ] No unnecessary dependencies added
- [ ] Follows existing patterns in codebase

## Project Context

### Technology Stack
- **Language**: Python 3.13
- **CLI Framework**: Typer
- **Testing**: pytest
- **Code Quality**: Black + Ruff + MyPy
- **Containerization**: Docker
- **Core Tool**: FFmpeg

### Key Files
- `cli_handler.py` - CLI entry point
- `src/cli/` - CLI commands
- `src/core/` - Business logic
- `src/ffmpeg/` - FFmpeg integration
- `src/config/` - Configuration models
- `tests/` - Test suite

### Configuration Requirements
- CLI requires `config.yaml` file
- Use sample from instructions or generate via `make docker-env`
- See `instructions/configuration.md` for details

## Error Handling

### Expected Errors
- File not found → Skip with warning, continue
- FFmpeg not available → Fail with clear message
- Timeout → Mark as timeout, continue
- Invalid config → Fail fast with validation error

### Logging
- Use Python logging module
- INFO for normal operations
- DEBUG for detailed diagnostics
- ERROR for failures with context
- WARNING for non-fatal issues

## Performance Considerations

### Optimization Strategies
- Use parallel processing for video scanning (multiprocessing)
- Implement appropriate timeouts (quick: 30s, deep: 30min)
- Cache results where beneficial
- Use generators for memory efficiency
- Profile before optimizing

### Resource Management
- Clean up resources after processing
- Handle timeouts gracefully
- Limit concurrent workers based on configuration
- Monitor memory usage for large file sets

## Useful Patterns

### Working with Videos
```python
# Quick scan
result = ffmpeg.run([
    "-v", "error",
    "-i", video_path,
    "-f", "null",
    "-"
], timeout=30)

# Check for corruption
if result.returncode != 0:
    # Video is corrupted
    pass
```

### Configuration Loading
```python
from pydantic import BaseModel

class Config(BaseModel):
    ffmpeg_command: str = "/usr/bin/ffmpeg"
    quick_timeout: int = 30
    
# Load from YAML
config = Config.parse_file("config.yaml")
```

### Testing with Fixtures
```python
@pytest.fixture
def temp_video_dir(tmp_path):
    video_dir = tmp_path / "videos"
    video_dir.mkdir()
    return video_dir

def test_scan_directory(temp_video_dir):
    result = scan_directory(str(temp_video_dir))
    assert result is not None
```

## Common Tasks

### Adding a New CLI Command
1. Create command in `src/cli/commands.py`
2. Register in `cli_handler.py`
3. Implement business logic in `src/core/`
4. Add tests in `tests/unit/` and `tests/integration/`
5. Update documentation in `docs/CLI.md`
6. Validate manually with config file

### Adding a New Configuration Option
1. Update Pydantic model in `src/config/models.py`
2. Update `config.sample.yaml`
3. Update documentation in `docs/CONFIG.md`
4. Add validation tests
5. Handle backward compatibility

### Fixing a Bug
1. Write failing test that reproduces bug
2. Fix the bug with minimal changes
3. Verify test now passes
4. Run `make check` and `make test`
5. Commit with `fix(component): description`

## Troubleshooting

### Import Errors
```bash
export PYTHONPATH=/path/to/repo/src
```

### Missing Config
```bash
# Create minimal config
cat > config.yaml << 'EOF'
logging:
  level: INFO
ffmpeg:
  command: /usr/bin/ffmpeg
  quick_timeout: 30
EOF
```

### Tool Versions
```bash
python --version   # Should be 3.13+
ffmpeg -version    # Should be installed
black --version    # Should be installed
```

## Continuous Improvement

### Feedback Loop
- Learn from code review feedback
- Update patterns based on successes
- Document common mistakes to avoid
- Share learnings in comments

### Instruction Updates
When project patterns change:
- Update relevant instruction files
- Keep agents.md current
- Document new conventions
- Remove outdated information

---

**For detailed information on specific topics**, refer to the modular instruction files:
- [General Instructions](../instructions/instructions.md)
- [Python Development](../instructions/python.md)
- [Configuration Management](../instructions/configuration.md)
- [Docker & Containerization](../instructions/docker.md)
- [Testing](../instructions/testing.md)
- [Git & Version Control](../instructions/git.md)
- [GitHub Actions & CI/CD](../instructions/github-actions.md)
- [Project-Specific Guidelines](../instructions/project-specific.md)
