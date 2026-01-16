---
name: documentation
description: Skill for creating and maintaining documentation in the Corrupt Video File Inspector project
---

# Documentation Skill

This skill provides comprehensive documentation capabilities including writing, updating, and maintaining project documentation.

## When to Use

Use this skill when:
- Creating new documentation for features
- Updating documentation after code changes
- Improving existing documentation clarity
- Writing user guides and tutorials
- Documenting APIs and configuration
- Generating code documentation (docstrings)

## Documentation Structure

### Project Documentation Layout

```
corruptvideofileinspector/
├── README.md                      # Main project overview
├── CHANGELOG.md                   # Version history and changes
├── CONTRIBUTING.md                # Contribution guidelines
├── LICENSE                        # License information
├── docs/                          # Detailed documentation
│   ├── CLI.md                    # CLI usage guide
│   ├── CONFIG.md                 # Configuration reference
│   ├── CORE.md                   # Core module documentation
│   ├── DOCKER.md                 # Docker usage guide
│   ├── FFMPEG.md                 # FFmpeg integration
│   ├── agents.md                 # Agent development guide
│   └── architecture.md           # Architecture overview
└── .github/
    ├── copilot-instructions.md   # Copilot agent instructions
    └── instructions/             # Module-specific instructions
```

## README Best Practices

### Essential README Sections

**1. Project Header**
```markdown
# Corrupt Video File Inspector

[![CI Status](badge-url)](link)
[![License](badge-url)](link)

Brief one-liner describing the project.
```

**2. Description**
```markdown
## Overview

Clear explanation of what the project does, why it exists, and who should use it.
Include key features and capabilities.
```

**3. Quick Start**
```markdown
## Quick Start

\`\`\`bash
# Clone repository
git clone <repo-url>
cd corruptvideofileinspector

# Install dependencies
make install-dev

# Run scan
corrupt-video-inspector scan /path/to/videos
\`\`\`
```

**4. Installation**
```markdown
## Installation

### Prerequisites
- Python 3.13+
- FFmpeg
- Docker (optional)

### Install Steps
1. Step one
2. Step two
3. Step three
```

**5. Usage Examples**
```markdown
## Usage

### Basic Scan
\`\`\`bash
corrupt-video-inspector scan /path/to/videos
\`\`\`

### Advanced Options
\`\`\`bash
corrupt-video-inspector scan /path --mode hybrid --output results.json
\`\`\`
```

**6. Configuration**
```markdown
## Configuration

Configuration file example and explanation of key options.
```

**7. Contributing**
```markdown
## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
```

## Markdown Standards

### Heading Hierarchy

```markdown
# H1 - Document Title (only one per file)

## H2 - Major Section

### H3 - Subsection

#### H4 - Minor Section

##### H5 - Rare, use sparingly
```

### Code Blocks

**Always specify language**
```markdown
\`\`\`python
def example_function() -> None:
    print("Hello, World!")
\`\`\`

\`\`\`bash
make test
\`\`\`

\`\`\`yaml
config:
  option: value
\`\`\`
```

### Lists

**Unordered Lists**
```markdown
- First item
- Second item
  - Nested item
  - Another nested item
- Third item
```

**Ordered Lists**
```markdown
1. First step
2. Second step
3. Third step
```

### Links and References

```markdown
# Inline link
[Link Text](https://example.com)

# Reference link
[Link Text][ref]

[ref]: https://example.com

# Internal link
[See Configuration](#configuration)
```

### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

### Code Inline

```markdown
Use backticks for `inline code` references.
```

### Emphasis

```markdown
*Italic text* or _italic text_
**Bold text** or __bold text__
***Bold and italic*** or ___bold and italic___
```

## Docstring Standards

### Google-Style Docstrings

**Function Documentation**
```python
def scan_video(path: Path, mode: str = "quick") -> ScanResult:
    """Scan a video file for corruption.
    
    Performs corruption detection using FFmpeg analysis. The scan mode
    determines the depth and duration of the analysis.
    
    Args:
        path: Path to the video file to scan
        mode: Scan mode - "quick", "deep", or "hybrid"
            - quick: Fast basic checks
            - deep: Comprehensive analysis
            - hybrid: Quick check followed by deep if issues found
    
    Returns:
        ScanResult object containing:
            - status: "healthy", "corrupt", or "error"
            - path: Path to scanned file
            - duration: Scan duration in seconds
            - errors: List of detected errors
    
    Raises:
        FileNotFoundError: If video file does not exist
        ValueError: If mode is invalid
        FFmpegError: If FFmpeg execution fails
    
    Examples:
        >>> result = scan_video(Path("/path/to/video.mp4"))
        >>> print(result.status)
        'healthy'
        
        >>> result = scan_video(Path("/path/to/video.mp4"), mode="deep")
        >>> if result.status == "corrupt":
        ...     print(f"Found {len(result.errors)} errors")
    """
    ...
```

**Class Documentation**
```python
class VideoScanner:
    """Scanner for detecting corrupt video files.
    
    This class provides methods for scanning video files using FFmpeg
    to detect corruption, format issues, and encoding problems.
    
    Attributes:
        config: Configuration object with FFmpeg settings
        timeout: Maximum scan duration in seconds
        logger: Logger instance for scan operations
    
    Examples:
        >>> config = Config.load()
        >>> scanner = VideoScanner(config)
        >>> result = scanner.scan(Path("/path/to/video.mp4"))
    """
    
    def __init__(self, config: Config) -> None:
        """Initialize scanner with configuration.
        
        Args:
            config: Configuration object with FFmpeg settings
        """
        ...
```

**Module Documentation**
```python
"""Video scanning module for corruption detection.

This module provides the core video scanning functionality using FFmpeg
to detect corrupt or damaged video files. It supports multiple scan modes
and provides detailed error reporting.

Typical usage example:
    from src.scanner import VideoScanner
    from src.config import Config
    
    config = Config.load()
    scanner = VideoScanner(config)
    result = scanner.scan(Path("/path/to/video.mp4"))
    
    if result.status == "corrupt":
        print(f"Video is corrupt: {result.errors}")
"""
```

### Docstring Requirements

**Required for:**
- All public functions and methods
- All public classes
- All modules
- Complex private functions (use judgment)

**Not required for:**
- Simple private methods
- Test functions (use descriptive test names instead)
- Property getters/setters (unless complex logic)

## API Documentation

### Configuration Reference

Document all configuration options with type, default, and description:

```markdown
## Configuration Options

### FFmpeg Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `command` | Path | `/usr/bin/ffmpeg` | Path to FFmpeg executable |
| `quick_timeout` | int | 30 | Timeout for quick scans (seconds) |
| `deep_timeout` | int | 1800 | Timeout for deep scans (seconds) |

Example configuration:
\`\`\`yaml
ffmpeg:
  command: /usr/bin/ffmpeg
  quick_timeout: 30
  deep_timeout: 1800
\`\`\`
```

### CLI Command Reference

Document all CLI commands with arguments, options, and examples:

```markdown
## CLI Commands

### scan

Scan a directory for corrupt video files.

**Usage:**
\`\`\`bash
corrupt-video-inspector scan [OPTIONS] DIRECTORY
\`\`\`

**Arguments:**
- `DIRECTORY`: Path to directory containing videos

**Options:**
- `--mode TEXT`: Scan mode (quick/deep/hybrid) [default: quick]
- `--output PATH`: Output file for results
- `--recursive/--no-recursive`: Scan subdirectories [default: recursive]

**Examples:**
\`\`\`bash
# Basic scan
corrupt-video-inspector scan /videos

# Deep scan with output
corrupt-video-inspector scan /videos --mode deep --output results.json

# Non-recursive scan
corrupt-video-inspector scan /videos --no-recursive
\`\`\`
```

## User Guides

### Tutorial Structure

```markdown
# How to [Task]

## Overview
Brief description of what you'll accomplish.

## Prerequisites
- Requirement 1
- Requirement 2

## Step 1: [First Action]
Detailed instructions for first step.
\`\`\`bash
command example
\`\`\`

## Step 2: [Second Action]
Detailed instructions for second step.

## Verification
How to verify the task completed successfully.

## Troubleshooting
Common issues and solutions.

## Next Steps
What to do after completing this tutorial.
```

### Example Tutorial

```markdown
# How to Set Up Trakt Integration

## Overview
This guide shows you how to configure Trakt.tv synchronization for your scan results.

## Prerequisites
- Trakt.tv account
- Trakt API credentials (client ID and secret)
- Corrupt Video Inspector installed

## Step 1: Get Trakt API Credentials

1. Log in to [Trakt.tv](https://trakt.tv)
2. Go to Settings > Your API Apps
3. Create a new application
4. Note your Client ID and Client Secret

## Step 2: Configure Secrets

Create secret files for your credentials:
\`\`\`bash
mkdir -p docker/secrets
echo "your-client-id" > docker/secrets/trakt_client_id.txt
echo "your-client-secret" > docker/secrets/trakt_client_secret.txt
\`\`\`

## Step 3: Update Configuration

Edit `config.yaml`:
\`\`\`yaml
trakt:
  enabled: true
  include_statuses: ["healthy"]
\`\`\`

## Step 4: Test Connection

\`\`\`bash
corrupt-video-inspector test-trakt
\`\`\`

## Verification

You should see:
\`\`\`
✓ Trakt connection successful
✓ Authentication validated
\`\`\`

## Troubleshooting

### Issue: Authentication Failed
**Solution**: Verify your client ID and secret are correct.

### Issue: Permission Denied
**Solution**: Ensure secret files have proper permissions (600).

## Next Steps
- Run a scan with Trakt sync enabled
- Configure which video statuses to sync
```

## Changelog Format

Follow [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New feature descriptions

### Changed
- Changes to existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes

## [1.2.0] - 2024-01-15

### Added
- Hybrid scan mode combining quick and deep analysis
- Trakt.tv integration for watchlist synchronization
- JSON output format support

### Fixed
- Timeout handling in deep scan mode
- Memory leak in video processing

## [1.1.0] - 2024-01-01

### Added
- Docker containerization support
- Configuration file validation

### Changed
- Improved CLI error messages
```

## Documentation Maintenance

### Regular Updates Needed

1. **After Code Changes**: Update affected documentation
2. **Before Releases**: Update CHANGELOG.md
3. **API Changes**: Update API reference documentation
4. **Configuration Changes**: Update configuration reference
5. **CLI Changes**: Update command reference

### Documentation Review Checklist

- [ ] All code examples are tested and working
- [ ] Version numbers are current
- [ ] Links are not broken
- [ ] Screenshots are up-to-date (if applicable)
- [ ] Configuration examples match current schema
- [ ] API documentation matches implementation
- [ ] Installation instructions are accurate
- [ ] Prerequisites are complete

## Examples and Code Samples

### Effective Examples

**Good Example: Complete and Runnable**
```python
from pathlib import Path
from src.scanner import VideoScanner
from src.config import Config

# Load configuration
config = Config.load("config.yaml")

# Initialize scanner
scanner = VideoScanner(config)

# Scan a video file
video_path = Path("/path/to/video.mp4")
result = scanner.scan(video_path)

# Check result
if result.status == "corrupt":
    print(f"Video is corrupt: {result.errors}")
elif result.status == "healthy":
    print("Video is healthy")
```

**Bad Example: Incomplete or Unclear**
```python
# Bad: Missing imports, unclear what 'result' is
result = scan(video)
if result:
    print("done")
```

### Example Requirements

- Include all necessary imports
- Show realistic usage scenarios
- Provide context for what the example demonstrates
- Include expected output or behavior
- Test that examples actually work

## References

- [Markdown Guide](https://www.markdownguide.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [Write the Docs](https://www.writethedocs.org/)
