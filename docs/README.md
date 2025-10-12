# Corrupt Video Inspector Documentation

Complete documentation for the Corrupt Video Inspector project.

## Quick Start Guides

- **[API Quick Start](API_QUICKSTART.md)**: Get started with the GraphQL API in 5 minutes
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to the project

## Core Documentation

- **[API Documentation](API.md)**: Complete FastAPI GraphQL API reference
- **[CLI Documentation](CLI.md)**: Command-line interface guide
- **[Core Module](CORE.md)**: Business logic and algorithms
- **[Configuration](CONFIG.md)**: Configuration system and options
- **[Database](DATABASE.md)**: SQLite database features and usage
- **[FFmpeg Integration](FFMPEG.md)**: Video processing and corruption detection
- **[Reporter](REPORTER.md)**: Report generation in multiple formats
- **[Utils](UTILS.md)**: Utility functions and helpers

## Docker & Deployment

- **[Docker Trakt Integration](DOCKER_TRAKT.md)**: Docker deployment with Trakt.tv sync
- **[Repository Configuration](REPOSITORY_CONFIGURATION.md)**: GitHub repository settings

## Development

- **[Contributing Guide](CONTRIBUTING.md)**: Development setup and guidelines
- **[Versioning](VERSIONING.md)**: Version management and releases
- **[PR Title Check](PR_TITLE_CHECK.md)**: Pull request title conventions
- **[Alpha Releases](ALPHA_RELEASES.md)**: Pre-release testing
- **[Changelog](CHANGELOG.md)**: Project history and changes

## Architecture

The project is organized into several modules:

```
src/
├── api/         # FastAPI GraphQL API
├── cli/         # Command-line interface
├── core/        # Core business logic
├── config/      # Configuration management
├── database/    # SQLite database support
├── ffmpeg/      # FFmpeg integration
└── utils/       # Shared utilities
```

## Getting Help

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/tdorsey/corruptvideofileinspector/issues)
- **Examples**: Check the `examples/` directory for working code samples
- **README**: See the main [README.md](../README.md) for project overview
