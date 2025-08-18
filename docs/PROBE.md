# FFprobe Integration and Probe-Before-Scan Workflow

This document describes the FFprobe integration and probe-before-scan workflow that ensures reliable video file analysis.

## Overview

The probe-before-scan workflow uses FFprobe to analyze files before corruption scanning, ensuring that:
- Only valid video files undergo resource-intensive corruption analysis
- Rich metadata is available for enhanced reporting
- Duplicate probe operations are avoided through caching
- Failed probes are handled gracefully

## Components

### ProbeResult Model
The `ProbeResult` class tracks FFprobe analysis results:

```python
from src.core.models.probe import ProbeResult

probe_result = ProbeResult(
    file_path=Path("/video.mp4"),
    success=True,
    streams=[video_stream, audio_stream],
    format_info=format_info,
    duration=120.5,
)

# Check if file is suitable for scanning
if probe_result.is_valid_video_file:
    print("File can be scanned for corruption")
```

### FFprobeClient
Executes FFprobe and parses JSON output:

```python
from src.ffmpeg.ffprobe_client import FFprobeClient
from src.config.config import FFmpegConfig

client = FFprobeClient(FFmpegConfig())
probe_result = client.probe_file(video_file)
```

### ProbeResultCache
Persistent caching to avoid redundant operations:

```python
from src.core.probe_cache import ProbeResultCache

cache = ProbeResultCache(Path("probe_cache.json"), max_age_hours=24.0)

# Check cache first
cached_result = cache.get(video_file.path)
if cached_result is None:
    # Probe and cache
    probe_result = client.probe_file(video_file)
    cache.put(probe_result)
```

## Configuration

Add probe settings to your configuration:

```yaml
ffmpeg:
  command: /usr/bin/ffmpeg
  probe_timeout: 15
  enable_probe_cache: true
  probe_cache_max_age_hours: 24.0
  require_probe_before_scan: true
```

### Configuration Options

- `probe_timeout`: Timeout for FFprobe operations (seconds)
- `enable_probe_cache`: Enable persistent caching of probe results
- `probe_cache_max_age_hours`: Maximum age for cached results
- `require_probe_before_scan`: Enforce probe-before-scan workflow

## Workflow

### 1. File Discovery
Scanner discovers video files in target directories.

### 2. Probe Phase
For each discovered file:
- Check cache for existing probe result
- If not cached or expired, run FFprobe
- Parse JSON output to extract streams and format info
- Cache result for future use

### 3. Eligibility Check
Files are eligible for scanning if:
- Probe was successful
- At least one video stream was detected
- Format information is available

### 4. Corruption Scanning
Only eligible files undergo corruption analysis:
- Probe results are passed to corruption scanner
- Enhanced reporting includes probe metadata

## CLI Commands

### Test FFprobe Installation
```bash
corrupt-video-inspector test-ffprobe /path/to/video.mp4
```

### Scan with Probe Workflow
The probe workflow is automatically enabled when `require_probe_before_scan: true`:

```bash
corrupt-video-inspector scan /path/to/videos --mode hybrid
```

## Output Enhancements

Scan results now include probe information:

```json
{
  "filename": "/path/to/video.mp4",
  "status": "HEALTHY",
  "probe_success": true,
  "has_video_streams": true,
  "probe_duration": 120.5,
  "probe_summary": "1 video, 1 audio streams, 120.5s"
}
```

## Performance Benefits

- **Reduced resource usage**: Skip non-video files early
- **Faster subsequent scans**: Cached probe results
- **Better error handling**: Clear separation of probe vs scan failures
- **Enhanced reporting**: Rich metadata for analysis

## Troubleshooting

### FFprobe Not Found
Ensure FFprobe is installed (usually comes with FFmpeg):
```bash
which ffprobe
ffprobe -version
```

### Cache Issues
Clear the probe cache if needed:
```bash
rm /path/to/output/probe_cache.json
```

### Probe Failures
Check FFprobe output manually:
```bash
ffprobe -v quiet -print_format json -show_format -show_streams /path/to/video.mp4
```

## Migration from Previous Versions

The probe workflow is optional and backward compatible:
- Set `require_probe_before_scan: false` to disable
- Existing scan results remain compatible
- No breaking changes to CLI or API

## Future Enhancements

Planned improvements:
- Database storage for probe cache
- Probe result expiration based on file modification time
- Advanced stream analysis and validation
- Integration with media information extraction