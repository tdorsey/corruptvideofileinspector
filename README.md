# Corrupt Video File Inspector

A comprehensive Python CLI tool for detecting corrupted video files using FFmpeg, with optional Trakt.tv synchronization and Docker containerization support.

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install corrupt-video-inspector

# Install from source
git clone https://github.com/tdorsey/corruptvideofileinspector.git
cd corruptvideofileinspector
pip install -e .

# Install with all optional dependencies
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Basic scan with hybrid mode (recommended)
corrupt-video-inspector scan /path/to/videos

# Quick scan with JSON output
corrupt-video-inspector scan --mode quick --output results.json /path/to/videos

# Sync scan results to Trakt.tv
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN
```

**For detailed usage instructions, see [CLI Module Documentation](docs/CLI.md)**

## ⚠️ API Changes & Migration

### get_all_video_object_files() Breaking Change (v0.6.0)

If you're programmatically using the `get_all_video_object_files()` function, note this breaking change:

- **Before**: Returns `list[Path]`
- **After**: Returns `list[VideoFile]` (provides richer metadata)
- **Migration**: Use `.path` property to access file paths, or temporarily use `as_paths=True` (deprecated)

```python
# New API (recommended)
video_files = get_all_video_object_files("/path/to/videos")
for video in video_files:
    print(f"Path: {video.path}, Size: {video.size}")

# Temporary compatibility (deprecated)
video_paths = get_all_video_object_files("/path/to/videos", as_paths=True)
```

See [CHANGELOG.md](CHANGELOG.md) and [CLI Documentation](docs/CLI.md) for full migration details.

## 📖 Documentation Overview

This project uses a modular documentation structure. Each major component has its own detailed documentation:

### 🔧 Core Components
- **[CLI Module](docs/CLI.md)** - Command-line interface and user interaction
- **[Core Engine](docs/CORE.md)** - Video scanning, inspection, and analysis algorithms
- **[FFmpeg Integration](docs/FFMPEG.md)** - Video corruption detection engine
- **[Configuration System](docs/CONFIG.md)** - Flexible configuration management

### 🎯 Features & Integration
- **[Trakt.tv Integration](docs/trakt.md)** - Watchlist synchronization and media management
- **[Report Generation](docs/REPORTER.md)** - Multi-format reporting (JSON, CSV, YAML, text)
- **[Utilities](docs/UTILS.md)** - Shared functions and helper tools

### 👨‍💻 Development
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Setup, code quality, and contribution process
- **[Version Management](docs/VERSIONING.md)** - Git tag-based dynamic versioning
- **[Testing](docs/tests.md)** - Test framework and execution

### Quick Reference

#### Scan Modes
- **Hybrid** (recommended): Quick scan + deep scan of suspicious files
- **Quick**: Fast 1-minute timeout per file
- **Deep**: Thorough 15-minute timeout per file

#### Key Features
- ✅ **Resume capability** with Write-Ahead Logging (WAL)
- ✅ **Multi-threaded processing** with configurable workers
- ✅ **Multiple output formats** (JSON, CSV, YAML, text)
- ✅ **Trakt.tv synchronization** for watchlist management
- ✅ **Docker support** for containerized workflows

**For complete usage instructions and examples, see the module-specific documentation above.**

## ⚙️ Configuration

The application supports flexible configuration through multiple sources with proper precedence handling:

1. **Command-line arguments** (highest precedence)
2. **Environment variables** (CVI_ prefix)
3. **Configuration files** (YAML/JSON)
4. **Docker secrets** (for containerized deployments)
5. **Built-in defaults** (lowest precedence)

### Quick Configuration Examples

```bash
# Generate sample configuration file
corrupt-video-inspector init-config --format yaml --output config.yml

# Use environment variables
export CVI_MAX_WORKERS=8
export CVI_LOG_LEVEL=DEBUG

# Use custom config file
corrupt-video-inspector scan --config my-config.yml /path/to/videos
```

**For complete configuration documentation, see [Configuration Guide](docs/CONFIG.md)**

## 🐳 Docker Usage

The application is designed to work seamlessly in containerized environments with full support for Trakt.tv integration:

```bash
# Build Docker image
docker build -t corrupt-video-inspector .

# Scan with volume mount
docker run -v /path/to/videos:/videos corrupt-video-inspector scan /videos

# Use docker-compose for complex workflows
docker-compose up scan report

# Include Trakt sync with docker-compose profiles
docker-compose --profile trakt up scan trakt
```

### Trakt.tv Integration with Docker

The Docker setup includes dedicated containers for Trakt.tv watchlist synchronization:

```bash
# Set required environment variables
export TRAKT_ACCESS_TOKEN="your_oauth_token"
export TRAKT_CLIENT_ID="your_client_id"
export CVI_VIDEO_DIR="/path/to/videos"
export CVI_OUTPUT_DIR="/path/to/output"

# Run complete workflow: scan + sync to Trakt
docker-compose --profile trakt up scan trakt

# Development mode with interactive Trakt sync
docker-compose -f docker/docker-compose.dev.yml --profile trakt up app trakt-dev
```

**For detailed Docker and Trakt container documentation, see:**
- **[Configuration Guide](docs/CONFIG.md)** - Docker secrets and environment setup
- **[Docker Trakt Guide](docs/DOCKER_TRAKT.md)** - Complete Trakt container documentation

## 🔧 Development

### Quick Development Setup

```bash
# Clone repository
git clone https://github.com/tdorsey/corruptvideofileinspector.git
cd corruptvideofileinspector

# Install system dependencies
make install-system-deps

# Install development dependencies
make install-dev

# Setup the project
make setup
```


```bash
# Scan a directory for corrupt videos
corrupt-video-inspector scan /path/to/videos --mode hybrid --output results.json

# View help for all commands
corrupt-video-inspector --help
```

**Note**: FFmpeg is a critical system dependency required for video analysis. The `make install-system-deps` command will install it automatically on most systems, or see [FFmpeg Installation](https://ffmpeg.org/download.html) for manual installation.

**For complete development documentation, see [Contributing Guide](docs/CONTRIBUTING.md)**

### Project Structure

```
corrupt_video_inspector/
├── src/
│   ├── cli/                    # Command-line interface → See docs/CLI.md
│   ├── core/                   # Core business logic → See docs/CORE.md
│   ├── config/                 # Configuration management → See docs/CONFIG.md
│   ├── ffmpeg/                 # FFmpeg integration → See docs/FFMPEG.md
│   └── utils/                  # Shared utilities → See docs/UTILS.md
├── tests/                      # Test suite → See docs/tests.md
├── docs/                       # Documentation
│   ├── CLI.md                  # Command-line interface documentation
│   ├── CORE.md                 # Core module documentation
│   ├── CONFIG.md               # Configuration system guide
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
