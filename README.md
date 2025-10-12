# Corrupt Video File Inspector

A comprehensive Python CLI tool for detecting corrupted video files using FFmpeg, with optional Trakt.tv synchronization and Docker containerization support.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/tdorsey/corruptvideofileinspector.git
cd corruptvideofileinspector

# Install system dependencies
make install-system-deps

# Install development dependencies
make install-dev

# Setup the project
make setup
```

### Basic Usage

```bash
# Scan a directory for corrupt videos
corrupt-video-inspector scan /path/to/videos --mode hybrid --output results.json

# Scan with database storage for historical tracking
corrupt-video-inspector scan /path/to/videos --database --mode hybrid

# Incremental scan (skip recently healthy files)
corrupt-video-inspector scan /path/to/videos --incremental --database

# Query database for corrupt files
corrupt-video-inspector database query --corrupt --since "7 days ago"

# View help for all commands
corrupt-video-inspector --help
```

### 🐳 Docker Usage

The application can be run in Docker containers with configurable user permissions:

#### Environment Variables

- **PUID** (default: 1000): User ID for the container runtime user
- **PGID** (default: 1000): Group ID for the container runtime user
- **COMPOSE_PROJECT_DIR**: Path to the directory containing docker-compose.yml (required for config file mount)
- **CVI_VIDEO_DIR**: Host path to video directory
- **CVI_OUTPUT_DIR**: Host path to output directory
- **CVI_LOG_DIR**: Host path to log directory

#### Prerequisites

- Set `COMPOSE_PROJECT_DIR` to the directory containing docker-compose.yml
- Ensure `config.yaml` exists at `${COMPOSE_PROJECT_DIR}/config.yaml`
- Host folders (videos, output, logs) should be owned or writable by the configured PUID/PGID

#### Usage Examples

```bash
# Set project directory (required for config file mount)
export COMPOSE_PROJECT_DIR=/path/to/corruptvideofileinspector/docker

# Set user/group IDs (optional, defaults to 1000)
export PUID=1000
export PGID=1000

# Set required volume paths
export CVI_VIDEO_DIR=/path/to/videos
export CVI_OUTPUT_DIR=/path/to/output
export CVI_LOG_DIR=/path/to/logs

# Run scan service
docker compose -f docker/docker-compose.yml up -d --build scan

# Run scan and generate report
docker compose -f docker/docker-compose.yml up -d --build scan report

# Run with Trakt sync (requires Trakt credentials)
docker compose -f docker/docker-compose.yml --profile trakt up -d --build scan trakt

# Run the GraphQL API server
docker compose -f docker/docker-compose.yml --profile api up -d api
```

For advanced Docker workflows and Trakt integration, see [Docker Trakt Integration](docs/DOCKER_TRAKT.md).

### 🌐 GraphQL API (New!)

FastAPI-based GraphQL API for web interface integration:

- **GraphQL Queries**: Query scan jobs, results, and summaries
- **GraphQL Mutations**: Start scans and generate reports via API
- **OIDC Authentication**: Secure API access with OpenID Connect
- **Docker Support**: Containerized API deployment
- **Web Integration Ready**: Enable web UI development

```bash
# Run API locally
make run-api

# Run API with Docker
make docker-api

# Access GraphQL playground
open http://localhost:8000/graphql
```

**See [API Documentation](docs/API.md) for complete GraphQL schema and examples.**

### 🗄️ Database Support

Optional SQLite database support enables persistent storage and advanced analysis:

- **Historical Tracking**: Maintain scan history across multiple runs
- **Incremental Scanning**: Skip recently scanned healthy files for faster scans
- **Advanced Querying**: SQL-like filters for corruption status, dates, confidence levels
- **Trend Analysis**: Track corruption rates and file health changes over time
- **Zero Configuration**: Embedded SQLite database requires no server setup

**See [Database Documentation](docs/DATABASE.md) for complete details and examples.**

**Note**: FFmpeg is a critical system dependency required for video analysis. The `make install-system-deps` command will install it automatically on most systems, or see [FFmpeg Installation](https://ffmpeg.org/download.html) for manual installation.

**For complete development documentation, see [Contributing Guide](docs/CONTRIBUTING.md)**

### Project Structure

```
corrupt_video_inspector/
├── src/
│   ├── api/                    # FastAPI GraphQL API → See docs/API.md
│   ├── cli/                    # Command-line interface → See docs/CLI.md
│   ├── core/                   # Core business logic → See docs/CORE.md
│   ├── config/                 # Configuration management → See docs/CONFIG.md
│   ├── database/               # SQLite database support → See docs/DATABASE.md
│   ├── ffmpeg/                 # FFmpeg integration → See docs/FFMPEG.md
│   └── utils/                  # Shared utilities → See docs/UTILS.md
├── tests/                      # Test suite → See docs/tests.md
├── docs/                       # Documentation
│   ├── API.md                  # FastAPI GraphQL API documentation
│   ├── CLI.md                  # Command-line interface documentation
│   ├── CORE.md                 # Core module documentation
│   ├── CONFIG.md               # Configuration system guide
│   ├── DATABASE.md             # SQLite database features and usage
│   ├── FFMPEG.md               # FFmpeg integration details
│   ├── UTILS.md                # Utilities documentation
│   ├── trakt.md                # Trakt.tv integration guide
│   ├── CONTRIBUTING.md         # Development setup and guidelines
│   ├── REPORTER.md             # Report generation system
│   └── VERSIONING.md           # Version management
└── pyproject.toml              # Project configuration
```

## 📊 Output Examples

The application generates comprehensive reports in multiple formats:

### JSON Report Summary
```json
{
  "scan_summary": {
    "total_files": 150,
    "corrupt_files": 3,
    "healthy_files": 147,
    "scan_mode": "hybrid",
    "success_rate": 98.0
  },
  "results": [
    {
      "filename": "/path/to/video.mp4",
      "is_corrupt": false,
      "confidence": 0.05,
      "scan_mode": "quick",
      "inspection_time": 2.3
    }
  ]
}
```

See [the usage document](docs/usage.md) for more details.

## 🤝 Contributing

We welcome contributions! To get started:

1. **Open an issue**: Describe the feature, bug fix, or improvement you'd like to make
2. **Automatic branch creation**: A branch will be automatically created for your issue (see [Automation](#-automation) below)
3. **Start development**: Follow the automatically posted instructions to check out your branch
4. **Follow code quality standards**: Use pre-commit hooks and project guidelines

### 📝 Conventional Commit Types

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for consistent commit messages and automated versioning. All pull requests must use one of these types in the title:

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New features or enhancements | `feat: add video batch processing` |
| `fix` | Bug fixes | `fix: resolve scanner timeout issues` |
| `docs` | Documentation changes | `docs: update installation guide` |
| `style` | Code style/formatting changes | `style: fix import organization` |
| `refactor` | Code refactoring without functional changes | `refactor: extract video validation logic` |
| `perf` | Performance improvements | `perf: optimize video scanning algorithm` |
| `test` | Test additions or improvements | `test: add integration tests for scanner` |
| `chore` | Maintenance tasks, dependencies | `chore: update Python dependencies` |
| `build` | Build system or dependency changes | `build: update Docker base image` |
| `ci` | CI/CD pipeline changes | `ci: add automated security scanning` |
| `revert` | Revert previous changes | `revert: undo problematic scanner changes` |

This repository implements security measures to protect critical configuration files:

- **CODEOWNERS**: Critical files have defined code owners (see `.github/CODEOWNERS`)
- **Branch Protection**: Main branch requires status checks and pull request reviews
- **Configuration Protection**: `.github/settings.yml` and security files have additional safeguards

For security policies and reporting vulnerabilities, see [SECURITY.md](SECURITY.md).

## 📞 Support & Resources

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/tdorsey/corruptvideofileinspector/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/tdorsey/corruptvideofileinspector/discussions)
- 📖 **Documentation**: See docs/ directory for detailed guides
- 🔄 **Contributing**: See [Contributing Guide](docs/CONTRIBUTING.md)
- 🔒 **Security**: See [Security Policy](SECURITY.md)

---

**Made with ❤️ for the media management community**

# Documentation

## Module Documentation

- **[CLI Module](docs/CLI.md)** - Command-line interface, commands, and handlers
- **[Core Module](docs/CORE.md)** - Business logic, scanning, inspection, and reporting
- **[Configuration](docs/CONFIG.md)** - Configuration system, environment variables, and Docker secrets
- **[FFmpeg Integration](docs/FFMPEG.md)** - Video analysis engine and corruption detection
- **[Utilities](docs/UTILS.md)** - Shared utilities and helper functions

## Integration and Usage

- **[Trakt.tv Integration](docs/trakt.md)** - Watchlist synchronization and media management
- **[Docker Trakt Integration](docs/DOCKER_TRAKT.md)** - Containerized Trakt.tv workflows and setup
- **[Report Generation](docs/REPORTER.md)** - Multi-format reporting system

## Development

- **[Contributing Guidelines](docs/CONTRIBUTING.md)** - Development setup, code quality, and submission process
- **[Repository Configuration](docs/REPOSITORY_CONFIGURATION.md)** - Repository settings management and code ownership
- **[Version Management](docs/VERSIONING.md)** - Dynamic versioning with Git tags
- **[Tests Documentation](docs/tests.md)** - Testing framework and test execution

[CI Badge]: https://github.com/rhysd/actionlint/workflows/CI/badge.svg?branch=main&event=push
[CI]: https://github.com/rhysd/actionlint/actions?query=workflow%3ACI+branch%3Amain
[api-badge]: https://pkg.go.dev/badge/github.com/rhysd/actionlint.svg
[apidoc]: https://pkg.go.dev/github.com/rhysd/actionlint
[repo]: https://github.com/rhysd/actionlint
[playground]: https://rhysd.github.io/actionlint/
[shellcheck]: https://github.com/koalaman/shellcheck
[pyflakes]: https://github.com/PyCQA/pyflakes
[act]: https://github.com/nektos/act
[syntax-doc]: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions
[filter-pattern-doc]: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#filter-pattern-cheat-sheet
[script-injection-doc]: https://docs.github.com/en/actions/learn-github-actions/security-hardening-for-github-actions#understanding-the-risk-of-script-injections
[issue-form]: https://github.com/rhysd/actionlint/issues/new
[releases]: https://github.com/rhysd/actionlint/releases
