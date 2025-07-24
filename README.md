# Corrupt Video Inspector 2.0

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive, modular tool for detecting corrupted video files using FFmpeg and optionally syncing healthy files to your Trakt.tv watchlist.

## ✨ Features

### 🔍 **Advanced Video Corruption Detection**
- **Three Scan Modes**: Quick (1min timeout), Deep (15min timeout), and Hybrid (intelligent combination)
- **FFmpeg Integration**: Leverages FFmpeg's robust video analysis capabilities
- **Intelligent Detection**: Advanced pattern matching for corruption indicators
- **Parallel Processing**: Multi-threaded scanning for improved performance

### 🔄 **Resume & Recovery**
- **Write-Ahead Logging (WAL)**: Automatically resume interrupted scans
- **Progress Tracking**: Real-time progress reporting with signal handling
- **Graceful Shutdown**: Handles interruptions cleanly with progress preservation

### 📺 **Trakt.tv Integration**
- **Watchlist Sync**: Automatically add healthy files to Trakt watchlist
- **Intelligent Parsing**: Extract movie/TV show info from filenames
- **Interactive Mode**: Manual selection when multiple matches found
- **Dry Run Support**: Preview sync operations before execution

### ⚙️ **Flexible Configuration**
- **Multiple Sources**: Environment variables, config files, Docker secrets
- **Profile Support**: Development, production, and custom profiles
- **Extensive Options**: Customize timeouts, workers, extensions, and more

### 📊 **Rich Output & Reporting**
- **Multiple Formats**: JSON, YAML, CSV output support
- **Detailed Reports**: Comprehensive scan summaries and statistics
- **Progress Visualization**: Real-time progress bars and status updates

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install corrupt-video-inspector

# Install from source
git clone https://github.com/yourusername/corrupt-video-inspector.git
cd corrupt-video-inspector
pip install -e .

# Install with all optional dependencies
pip install -e ".[all]"
```

### Basic Usage

```bash
# Basic scan with hybrid mode (recommended)
corrupt-video-inspector scan /path/to/videos

# Quick scan only
corrupt-video-inspector scan --mode quick /path/to/videos

# Deep scan with custom output
corrupt-video-inspector scan --mode deep --output results.json /path/to/videos

# List video files without scanning
corrupt-video-inspector list-files /path/to/videos

# Sync scan results to Trakt.tv
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN
```

## 📖 Usage Guide

### Scanning Videos

The core functionality revolves around three scan modes:

#### **Hybrid Mode (Recommended)**
Combines the speed of quick scanning with the thoroughness of deep scanning:

```bash
corrupt-video-inspector scan --mode hybrid /path/to/videos
```

1. **Phase 1**: Quick scan all files (1-minute timeout each)
2. **Phase 2**: Deep scan only files flagged as suspicious

#### **Quick Mode**
Fast scanning with 1-minute timeout per file:

```bash
corrupt-video-inspector scan --mode quick /path/to/videos
```

#### **Deep Mode**
Thorough scanning with 15-minute timeout per file:

```bash
corrupt-video-inspector scan --mode deep /path/to/videos
```

### Advanced Options

```bash
# Custom worker threads and extensions
corrupt-video-inspector scan \
  --mode hybrid \
  --max-workers 8 \
  --extensions mp4 mkv avi \
  --output detailed_results.json \
  /path/to/videos

# Non-recursive scan
corrupt-video-inspector scan --no-recursive /path/to/videos

# Disable resume functionality
corrupt-video-inspector scan --no-resume /path/to/videos
```

### Trakt.tv Integration

First, obtain a Trakt.tv API token from [Trakt.tv API settings](https://trakt.tv/oauth/applications).

```bash
# Basic sync
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN

# Interactive mode (manual selection for multiple matches)
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --interactive

# Dry run (see what would be synced)
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --dry-run

# Include corrupt files in sync
corrupt-video-inspector trakt sync results.json --token YOUR_TOKEN --include-corrupt
```

## ⚙️ Configuration

### Configuration File

Generate a sample configuration:

```bash
corrupt-video-inspector init-config --format yaml --output config.yml
```

Example configuration:

```yaml
# config.yml
scanner:
  max_workers: 4
  default_mode: "hybrid"
  recursive: true
  extensions: [".mp4", ".mkv", ".avi", ".mov", ".wmv"]

ffmpeg:
  quick_timeout: 60
  deep_timeout: 900
  command: "/usr/bin/ffmpeg"  # auto-detect if not specified

trakt:
  client_id: "your_trakt_client_id"
  client_secret: "your_trakt_client_secret"

logging:
  level: "INFO"
  file: "/var/log/cvi.log"  # optional

output:
  default_format: "json"
  pretty_print: true
```

### Environment Variables

All configuration options can be set via environment variables:

```bash
export CVI_MAX_WORKERS=8
export CVI_LOG_LEVEL=DEBUG
export CVI_FFMPEG_COMMAND=/usr/local/bin/ffmpeg
export TRAKT_CLIENT_ID=your_client_id
export TRAKT_CLIENT_SECRET=your_client_secret
```

### Docker Secrets

For containerized deployments, use Docker secrets:

```bash
# Create secrets
echo "your_client_id" | docker secret create trakt_client_id -
echo "your_client_secret" | docker secret create trakt_client_secret -

# Secrets are automatically loaded from /run/secrets/
```

## 🐳 Docker Usage

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Install application
COPY . /app
WORKDIR /app
RUN pip install -e .

ENTRYPOINT ["corrupt-video-inspector"]
```

```bash
# Build and run
docker build -t corrupt-video-inspector .

# Scan with volume mount
docker run -v /path/to/videos:/videos corrupt-video-inspector scan /videos

# Use docker-compose for complex setups
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/corrupt-video-inspector.git
cd corrupt-video-inspector

# Install in development mode with all dependencies
pip install -e ".[dev,docs,reporting]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=corrupt_video_inspector --cov-report=html

# Format code
black src tests
isort src tests

# Type checking
mypy src
```

### Project Structure

```
corrupt_video_inspector/
├── src/corrupt_video_inspector/
│   ├── cli/                    # Command-line interface
│   ├── core/                   # Core business logic
│   ├── config/                 # Configuration management
│   ├── integrations/           # External service integrations
│   │   ├── ffmpeg/            # FFmpeg integration
│   │   └── trakt/             # Trakt.tv integration
│   ├── storage/               # Data persistence layer
│   └── utils/                 # Shared utilities
├── tests/                     # Test suite
├── docs/                      # Documentation
└── scripts/                   # Utility scripts
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m "not slow"           # Skip slow tests
pytest -m "unit"               # Unit tests only
pytest -m "integration"        # Integration tests only

# Run with specific fixtures
pytest -m "ffmpeg"             # Tests requiring FFmpeg
pytest -m "network"            # Tests requiring network access
```

## 📊 Output Formats

### JSON Output
```json
{
  "scan_summary": {
    "total_files": 150,
    "corrupt_files": 3,
    "healthy_files": 147,
    "scan_mode": "hybrid",
    "scan_time": 1234.56,
    "success_rate": 98.0
  },
  "results": [
    {
      "filename": "/path/to/video.mp4",
      "is_corrupt": false,
      "scan_mode": "quick",
      "inspection_time": 2.3,
      "file_size": 1073741824
    }
  ]
}
```

### CSV Output
Suitable for spreadsheet analysis and reporting.

### YAML Output
Human-readable format for configuration and review.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format code (`black src tests && isort src tests`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Style

- Follow [PEP 8](https://pep8.org/) guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Add type hints for all public APIs
- Write docstrings for all public functions and classes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FFmpeg](https://ffmpeg.org/) for video analysis capabilities
- [Trakt.tv](https://trakt.tv/) for providing the API for media tracking
- [Click](https://click.palletsprojects.com/) for the excellent CLI framework
- The Python community for the fantastic ecosystem of tools

## 📞 Support

- 📧 **Email**: your.email@example.com
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/corrupt-video-inspector/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/corrupt-video-inspector/discussions)
- 📖 **Documentation**: [Read the Docs](https://corrupt-video-inspector.readthedocs.io/)

---

**Made with ❤️ for the media management community**
