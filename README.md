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

**Supported formats**: JSON, CSV, YAML, Plain Text

**For detailed report structure and examples, see [Report Generation Documentation](docs/REPORTER.md)**

**GitHub Actions Workflow Validation:**
- PRs that add or modify GitHub Actions workflow files (`.github/workflows/*.yml` or `.github/workflows/*.yaml`) are automatically validated for syntax correctness
- The workflow validation check uses `actionlint` via the `devops-actions/actionlint@v0.1.9` marketplace action to ensure proper GitHub Actions syntax
- PRs with invalid workflow syntax will be blocked from merging until issues are resolved
- This validation runs automatically and is a required check

### Code Quality Standards
- **Formatting**: Black (100 character line length)
- **Linting**: Ruff with comprehensive rule set
- **Type Checking**: MyPy with strict configuration
- **Testing**: Comprehensive test coverage
- **Workflow Validation**: GitHub Actions syntax validation with actionlint

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

**Pull Request Title Format**: `type: description` (e.g., `feat: add new video validation feature`)

Issue templates are available for each type to guide your contribution. The automated systems will label and process your contribution based on the type you choose.

5. **Add tests**: Include tests for new functionality
6. **Submit a Pull Request**: Use conventional commit format and reference the issue

### 🤖 Automation

**Automatic Branch Creation**: When you open a new issue, our GitHub Actions workflow automatically:
- Creates a new branch named `issue-<number>-<slug>` based on your issue title
- Posts a comment with branch information and development instructions
- Provides ready-to-use git commands for getting started

**Example**: Issue #123 titled "Add progress bar feature" creates branch `issue-123-add-progress-bar-feature`

### Pull Request Requirements
**All PR titles must follow conventional commit format and reference an issue:**
```
type: description (#issue-number)
```
Examples: `feat: add progress bar (#123)`, `fix: resolve timeout issue (#456)`

### Code Quality Standards
- **Formatting**: Black (100 character line length)
- **Linting**: Ruff with comprehensive rule set
- **Type Checking**: MyPy with strict configuration
- **Testing**: Comprehensive test coverage

**For detailed contribution guidelines, see [Contributing Guide](docs/CONTRIBUTING.md)**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FFmpeg](https://ffmpeg.org/) for video analysis capabilities
- [Trakt.tv](https://trakt.tv/) for providing the API for media tracking
- [Click](https://click.palletsprojects.com/) for the excellent CLI framework
- The Python community for the fantastic ecosystem of tools

## 🔒 Security

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
