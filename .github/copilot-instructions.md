# Corrupt Video Inspector - Copilot Instructions

A comprehensive Python CLI tool for detecting corrupted video files using FFmpeg, with optional Trakt.tv synchronization and Docker containerization support.

## 📚 Modular Instruction Files

This project uses **modular instructions** for better performance and maintainability. Each file focuses on a specific aspect of development:

### Core Development
- **[General Instructions](../instructions/instructions.md)** - Project overview, setup, and common commands
- **[Python Development](../instructions/python.md)** - Python patterns, code quality, and CLI development
- **[Configuration Management](../instructions/configuration.md)** - Environment variables, config files, secrets
- **[Docker & Containerization](../instructions/docker.md)** - Docker builds, compose files, container workflows
- **[Testing](../instructions/testing.md)** - Test structure, fixtures, and testing patterns

### Version Control & CI/CD
- **[Git & Version Control](../instructions/git.md)** - Commit conventions, branching, and PR requirements
- **[GitHub Actions & CI/CD](../instructions/github-actions.md)** - Workflow patterns and marketplace actions
- **[Workflow File Instructions](../instructions/workflows.md)** - Workflow commit guidelines

### Project Knowledge
- **[Project-Specific Guidelines](../instructions/project-specific.md)** - Architecture, entry points, patterns
- **[Complete Reference](../instructions/copilot-instructions.md)** - Master reference and navigation guide

## 🚀 Quick Start

### Key Project Context
- **Language**: Python 3.13 with strict type checking
- **Build System**: pyproject.toml with Poetry
- **Testing**: pytest with unit/integration separation
- **Code Quality**: Black + Ruff + MyPy via `make check`
- **CLI**: Typer framework
- **Containerization**: Docker with multi-stage builds
- **Core Dependency**: FFmpeg for video analysis

### Essential Commands
```bash
make check              # Format, lint, type check (MUST pass before commit)
make test               # Run all tests
make docker-env         # Generate Docker environment
export PYTHONPATH=src   # Enable imports without installation
```

### Copilot Agent Environment
- **Pre-installed**: FFmpeg, build-essential, all Python dev dependencies
- **No Network Required**: Testing, linting, formatting work offline
- **Network Required**: Only for new dependency installation locally
## ⚙️ Development Standards (REQUIRED)

### Commit Standards
**All commits MUST follow [Conventional Commits](https://www.conventionalcommits.org/):**
- Format: `<type>[optional scope]: <description>` (lowercase description)
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
- Examples: `feat(cli): add video scan command`, `fix(config): resolve parsing error`
- See [Git & Version Control](../instructions/git.md) for details

### Code Quality
- **⚠️ CRITICAL: `make check` MUST pass before every commit**
- All tests must pass before submitting changes
- Update `poetry.lock` when modifying dependencies
- Resolve all merge conflicts before PR submission

### Pull Request Requirements
- Pass all CI/CD checks (formatting, linting, type checking, tests)
- Update `poetry.lock` if dependencies changed
- Resolve merge conflicts (run `git status` and `git diff` to verify)

## 🎯 GitHub Copilot Usage Best Practices

### For Copilot Agents
1. **Load relevant modular instructions** - use topic-specific files
2. **Follow existing patterns** - match repository code style
3. **Make minimal changes** - surgical modifications only
4. **Test thoroughly** - validate all changes before reporting progress
5. **Use report_progress tool** - commit and push changes

### Primary Use Cases

#### Code Implementation & Refactoring
- Write Python functions with proper type annotations
- Implement FFmpeg integration and video processing logic
- Create CLI commands using Typer framework
- Build Pydantic configuration models

#### Testing & Quality Assurance
- Write unit tests with `@pytest.mark.unit` markers
- Create integration tests for video workflows
- Debug test failures and improve coverage
- Implement test fixtures for video scenarios

#### Docker & Containerization
- Optimize Dockerfile multi-stage builds
- Setup docker-compose workflows
- Troubleshoot container environment issues
- Implement container-based testing

#### Configuration & Environment Setup
- Setup environment variables and config files
- Create Pydantic configuration models
- Manage Docker secrets and environment settings
- Troubleshoot CLI configuration

### Code Review Focus Areas
- Black formatting, Ruff linting, MyPy type checking compliance
- Proper type annotations and Python best practices
- No hardcoded secrets or security vulnerabilities
- Appropriate unit test coverage with pytest markers
- Documentation updates for public APIs

## 📖 Additional Resources

- **[CHANGELOG.md](../CHANGELOG.md)** - Latest updates and changes
- **Detailed Documentation**: `docs/` directory for module-specific docs
- **Issue Templates**: `.github/ISSUE_TEMPLATE/` - Required for all issues
- **Workflow Documentation**: `.github/workflows/README.md`

## 🛠️ Issue Creation Guidelines

### Required Templates
- **Template selection is enforced** (blank issues disabled)
- **Quick Capture** recommended for unstructured input (auto-triaged by agent)
- Available: Feature Request, Bug Report, Docs, Testing, Chore, Performance, Refactor, Style

### Issue Triage Agent
- Automatically processes Quick Capture issues
- Classifies type (bug, feature, docs, performance, task)
- Applies appropriate labels and reformats body
- Resources: `.github/agents/issue-creation-agent.md`, `.github/skills/issue-creation/SKILL.md`

## 🚦 Quick Reference Summary

### Critical Commands
```bash
make check              # ⚠️ MUST pass before commit
make test               # Validate all functionality
export PYTHONPATH=src   # Enable imports without install
```

### Development Workflow
1. Load relevant instruction file for your task
2. Make minimal, focused changes
3. Run `make check` (must pass)
4. Run targeted tests
5. Use `report_progress` to commit

### Timing Expectations
- `make check`: 30-60 sec (timeout 5+ min)
- Unit tests: 30 sec-2 min (timeout 10+ min)
- Full test suite: 1-15 min (timeout 30+ min)
- Docker builds: 5-15 min (timeout 30+ min)

### Common Issues
- **Import errors**: `export PYTHONPATH=/path/to/repo/src`
- **CLI config errors**: CLI requires valid `config.yaml` file
- **Test failures**: Check FFmpeg installation and file permissions
- **Network timeouts**: Use Docker as fallback for local dev

---

**Remember**: These instructions use a modular structure for optimal Copilot performance. Always reference the specific instruction file relevant to your task.
