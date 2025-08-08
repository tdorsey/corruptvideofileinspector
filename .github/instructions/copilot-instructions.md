# GitHub Copilot Instructions Overview

## Instruction Files Organization

This repository uses multiple specialized instruction files to provide targeted guidance for different aspects of development. Please refer to the appropriate instruction files based on your current task:

### Available Instruction Files

1. **[python.md](./python.md)** - Python development standards, code quality, type annotations, and best practices
2. **[testing.md](./testing.md)** - Testing guidelines, test structure, and containerized testing workflows
3. **[docker.md](./docker.md)** - Docker and containerization instructions, environment management, and deployment practices
4. **[configuration.md](./configuration.md)** - Environment variable management, configuration validation, and security practices
5. **[git.md](./git.md)** - Git workflow, commit message standards, and version control best practices
6. **[github-actions.md](./github-actions.md)** - GitHub Actions workflows, CI/CD pipelines, and automation best practices
7. **[project-specific.md](./project-specific.md)** - Project architecture, specific patterns, and development workflow for this codebase

## How to Use These Instructions

### For Python Development Tasks
- Review **python.md** for code standards, type hints, and quality requirements
- Check **project-specific.md** for project architecture and module organization

### For Testing Work
- Follow **testing.md** for test structure and containerized testing
- Reference **docker.md** for running tests in containers

### For Configuration Changes
- Use **configuration.md** for environment variable management
- Check **docker.md** for containerization-specific configuration

### For Docker and Deployment
- Primary reference: **docker.md** for all containerization needs
- Supplement with **configuration.md** for environment management

### For CI/CD and GitHub Actions
- Use **github-actions.md** for workflow development and debugging
- Reference **testing.md** for CI-compatible test execution
- Check **docker.md** for CI Docker builds and deployment

### For Version Control
- Follow **git.md** for commit messages and branch management
- Reference **project-specific.md** for project-specific workflow

## General Development Principles

### Code Quality First
- Always run code quality checks before committing
- Use containerized development environment
- Follow established project patterns and conventions

### Documentation and Configuration
- Document all environment variables in `.env.example`
- Update relevant instruction files when patterns change
- Maintain clear commit messages following Conventional Commits

### Security and Best Practices
- Never commit secrets or sensitive information
- Use proper environment variable management
- Follow container security best practices

---

**Note**: These instruction files are designed to work together. When working on a task that spans multiple areas (e.g., adding a new feature that requires code changes, tests, and configuration), refer to multiple instruction files as needed.
