# Docker Secrets Directory

This directory contains Docker secrets for the corrupt-video-inspector application.

## Supported Secrets

- `cvi_log_level.txt` - Override logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `cvi_ffmpeg_command.txt` - Override ffmpeg command path

## Usage

Create text files with the desired values:

```bash
echo "DEBUG" > secrets/cvi_log_level.txt
echo "/usr/local/bin/ffmpeg" > secrets/cvi_ffmpeg_command.txt
```

## Security Note

Never commit actual secret files to version control. The secret files themselves are ignored in .gitignore.