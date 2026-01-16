# Complete Copilot Instructions

This is the master reference for all GitHub Copilot usage in the Corrupt Video File Inspector project.

## Overview

These instructions are organized into modular files for better navigation and maintainability. Each file focuses on a specific aspect of development.

## Instruction Files

### Core Development Guides
- **[General Instructions](instructions.md)** - Project overview, getting started, and basic setup
- **[Python Development](python.md)** - Python-specific development patterns and project structure
- **[Configuration Management](configuration.md)** - Environment variables, configuration files, and secrets
- **[Docker & Containerization](docker.md)** - Docker builds, compose files, and container workflows
- **[Testing](testing.md)** - Test structure, containerized testing, and testing patterns

### Version Control & CI/CD
- **[Git & Version Control](git.md)** - Commit conventions, branching strategies, and version control
- **[GitHub Actions & CI/CD](github-actions.md)** - Workflow patterns, marketplace actions, and automation
- **[Workflow File Commit Instructions](workflows.md)** - Commit message and review guidelines for workflow files

### Project Knowledge
- **[Project-Specific Guidelines](project-specific.md)** - Architecture, key entry points, and project-specific patterns

## Quick Navigation

### I want to...

#### Get Started
→ Start with [General Instructions](instructions.md)

#### Write Python Code
→ See [Python Development](python.md)

#### Configure the Application
→ See [Configuration Management](configuration.md)

#### Work with Docker
→ See [Docker & Containerization](docker.md)

#### Write Tests
→ See [Testing](testing.md)

#### Make Git Commits
→ See [Git & Version Control](git.md)

#### Modify CI/CD
→ See [GitHub Actions & CI/CD](github-actions.md)

#### Understand the Architecture
→ See [Project-Specific Guidelines](project-specific.md)

## Key Principles

### Code Quality
1. **Always run `make check` before committing** - ensures formatting, linting, and type checking pass
2. **Write tests for new functionality** - use pytest with appropriate markers
3. **Follow conventional commits** - all commits must use conventional format
4. **Update documentation** - keep docs in sync with code changes

### Development Workflow
1. **Start with exploration** - understand existing code before changes
2. **Make minimal changes** - smallest possible changes to achieve goals
3. **Test incrementally** - validate changes as you make them
4. **Report progress frequently** - use report_progress tool after meaningful work

### Performance Optimization
1. **Use modular instructions** - load only what you need
2. **Cache aggressively** - leverage caching in CI/CD
3. **Prefer marketplace actions** - avoid custom workflow code
4. **Profile before optimizing** - measure actual bottlenecks

## Copilot Environment

### Pre-installed Dependencies
- FFmpeg and build-essential (system)
- All Python dev dependencies (black, ruff, mypy, pytest)
- Poetry for dependency management
- Docker for containerization

### No Network Required
- Testing works offline
- Linting and formatting work offline
- Type checking works offline
- Basic CLI testing works offline

### Network Required (Local Dev Only)
- Installing new dependencies (`make install-dev`)
- Building Docker images (`make docker-build`)
- Pulling from PyPI or Docker Hub

## GitHub Copilot Usage Best Practices

### Context Optimization
- **Modular instructions**: Each file <10KB for faster loading
- **Clear file organization**: Easy to find relevant information
- **Consistent formatting**: Scannable structure with headers
- **Cross-references**: Links between related topics

### Effective Prompting
- **Be specific**: "Implement video scanning in src/core/scanner.py"
- **Provide context**: Reference existing patterns and conventions
- **Set expectations**: Specify test requirements and validation
- **Iterate**: Refine based on results

### Code Generation
- **Follow existing patterns**: Match repository style
- **Use type hints**: All public APIs need annotations
- **Write tests**: Include unit tests with markers
- **Document**: Add docstrings for public APIs

### Code Review
- **Check standards**: Formatting, linting, type checking
- **Verify tests**: Appropriate test coverage
- **Review security**: No hardcoded secrets, proper validation
- **Check documentation**: Updated docs and comments

## Project Context

### Technology Stack
- **Language**: Python 3.13 with strict type checking
- **Build System**: pyproject.toml with Poetry
- **Testing**: pytest with unit/integration separation
- **Code Quality**: Black + Ruff + MyPy
- **CLI**: Typer framework
- **Containerization**: Docker with multi-stage builds
- **Core Dependency**: FFmpeg for video analysis

### Repository Structure
```
corruptvideofileinspector/
├── .github/               # GitHub configuration and workflows
│   ├── agents/           # Custom Copilot agents
│   ├── skills/           # Copilot skills
│   └── workflows/        # CI/CD workflows
├── docs/                 # Detailed documentation
├── instructions/         # This directory - Copilot instructions
├── src/                  # Main source code
│   ├── cli/             # CLI interface
│   ├── core/            # Business logic
│   ├── config/          # Configuration
│   └── ffmpeg/          # FFmpeg integration
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── docker/             # Docker configuration
├── pyproject.toml      # Project configuration
├── Makefile           # Development automation
└── README.md          # Project documentation
```

## Common Commands

### Essential
```bash
make help              # Show all available commands
make check             # Format, lint, and type check
make test              # Run all tests
make docker-env        # Generate Docker environment files
make secrets-init      # Initialize Trakt secrets
```

### Development
```bash
make install-dev       # Install development dependencies
make pre-commit-install # Setup code quality hooks
make format            # Format code with black
make lint              # Lint code with ruff
make type              # Type check with mypy
```

### Docker
```bash
make docker-build      # Build production image
make dev-build         # Build development image
make dev-shell         # Interactive container shell
make docker-scan       # Run video scan via Docker
```

### Testing
```bash
make test              # All tests
make test-integration  # Integration tests only
pytest tests/ -v -m "unit"  # Unit tests only
make test-cov          # Tests with coverage
```

## Troubleshooting

### Common Issues
- **Import errors**: Set `PYTHONPATH=$(pwd)/src`
- **CLI requires config**: Use sample config or `make docker-env`
- **Tests fail**: Check FFmpeg installation
- **Docker issues**: Ensure Docker service is running

### Getting Help
1. Check the relevant instruction file
2. Review existing code patterns
3. Check documentation in `docs/`
4. Examine test cases for examples

## Best Practices Summary

### For Copilot Agents
1. **Load relevant instructions** - use modular files
2. **Follow existing patterns** - match repository style
3. **Make minimal changes** - surgical modifications only
4. **Test thoroughly** - validate all changes
5. **Report progress** - use report_progress tool

### For Developers
1. **Keep instructions updated** - sync with code changes
2. **Write clear commits** - use conventional format
3. **Add tests** - cover new functionality
4. **Document changes** - update relevant docs
5. **Review before merge** - ensure quality standards

## Continuous Improvement

### Instruction Maintenance
- Update instructions when patterns change
- Add new files for new major features
- Keep file sizes manageable (<10KB)
- Maintain cross-references
- Remove outdated information

### Performance Monitoring
- Monitor Copilot response times
- Optimize instruction loading
- Cache frequently used content
- Profile agent performance

### Feedback Loop
- Collect agent performance data
- Identify common issues
- Refine instructions based on usage
- Share learnings across team

## Additional Resources

- **Project README**: `/README.md`
- **Changelog**: `/CHANGELOG.md`
- **Detailed Documentation**: `/docs/`
- **Issue Templates**: `.github/ISSUE_TEMPLATE/`
- **Workflow Documentation**: `.github/workflows/README.md`

---

**Remember**: These instructions are designed to help both human developers and AI agents work effectively with this codebase. Keep them current, clear, and concise.
