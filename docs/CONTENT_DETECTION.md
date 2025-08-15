# FFprobe Content-Based Video Detection

## Overview

Starting in version 1.x, Corrupt Video Inspector supports **content-based video file detection** using FFprobe analysis instead of relying solely on file extensions. This provides more accurate video file identification and reduces false positives.

## How It Works

### Traditional Extension-Based Detection
```python
# Old approach - check file extension only
if file_path.suffix.lower() in [".mp4", ".avi", ".mkv"]:
    process_as_video(file_path)
```

**Problems:**
- Files with video extensions but non-video content are processed
- Video files with missing/wrong extensions are skipped
- Requires manual maintenance of extension lists

### New Content-Based Detection
```python
# New approach - analyze actual file content
streams = ffprobe.analyze_streams(file_path)
if any(stream.get('codec_type') == 'video' for stream in streams):
    process_as_video(file_path)
```

**Benefits:**
- Identifies video files by actual content, not filename
- Rejects fake video files (e.g., text files with .mp4 extension)
- Automatically supports new video formats as FFprobe is updated
- No manual extension list maintenance required

## Configuration

### Enable Content Detection (Default)
```yaml
scan:
  use_content_detection: true
  ffprobe_timeout: 30
  extension_filter: []
```

### Disable Content Detection (Extension-Only)
```yaml
scan:
  use_content_detection: false
  extensions: [".mp4", ".mkv", ".avi", ".mov"]
```

### Performance Optimization
```yaml
scan:
  use_content_detection: true
  extension_filter: [".mp4", ".mkv", ".avi"]  # Pre-filter for performance
  ffprobe_timeout: 15                         # Faster timeout
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `use_content_detection` | bool | `true` | Enable FFprobe content analysis |
| `ffprobe_timeout` | int | `30` | Timeout in seconds for FFprobe analysis |
| `extension_filter` | list | `[]` | Optional extensions to pre-filter before analysis |

### Extension Filter Behavior

- **Empty list** (`[]`): Analyze all files (slower but most accurate)
- **With extensions** (`[".mp4", ".mkv"]`): Only analyze files with these extensions first
- Performance optimization: Skip FFprobe for files not matching filter

## Error Handling & Fallbacks

The system includes multiple fallback mechanisms:

1. **FFmpeg Client Initialization Failure**: Falls back to extension-based detection
2. **FFprobe Command Not Found**: Falls back to extension-based detection  
3. **Individual File Analysis Failure**: Falls back to extension check for that file
4. **Timeout on Analysis**: Falls back to extension check for that file

## Examples

### Example 1: Strict Content Detection
```yaml
scan:
  use_content_detection: true
  extension_filter: []        # Analyze all files
  ffprobe_timeout: 60        # Allow more time for analysis
```

**Result**: Most accurate detection, slower performance

### Example 2: Performance Optimized
```yaml
scan:
  use_content_detection: true
  extension_filter: [".mp4", ".mkv", ".avi", ".mov"]
  ffprobe_timeout: 15
```

**Result**: Good balance of accuracy and performance

### Example 3: Extension-Only (Legacy)
```yaml
scan:
  use_content_detection: false
  extensions: [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"]
```

**Result**: Fastest performance, less accurate

## CLI Usage

Content detection settings are configured through the YAML configuration file. The CLI will automatically use the configured detection method.

```bash
# Uses content detection if enabled in config
corrupt-video-inspector scan /path/to/videos

# Show current configuration including detection method
corrupt-video-inspector show-config
```

## Compatibility

- **Backward Compatible**: Existing configurations work unchanged
- **Default Behavior**: Content detection is enabled by default for new configurations
- **Migration**: Existing `extensions` setting is preserved as fallback

## Troubleshooting

### Content Detection Not Working
1. Verify FFprobe is available: `ffprobe -version`
2. Check configuration: `use_content_detection: true`
3. Review logs for FFmpeg client initialization errors
4. Test with known video files first

### Performance Issues
1. Add `extension_filter` to pre-filter files
2. Reduce `ffprobe_timeout` for faster processing
3. Consider disabling for very large directories
4. Use `mode: quick` for basic scanning

### False Negatives (Missing Videos)
1. Check if `extension_filter` is too restrictive
2. Verify video files are not corrupted beyond FFprobe's ability to read
3. Increase `ffprobe_timeout` for complex files
4. Review logs for analysis failures

## Technical Details

### FFprobe Command Used
```bash
ffprobe -v quiet -print_format json -show_streams /path/to/file
```

### Stream Analysis Logic
```python
def is_video_file(self, file_path: Path) -> bool:
    streams = self.analyze_streams(file_path)
    return any(stream.get("codec_type") == "video" 
              for stream in streams.get("streams", []))
```

### Timeout Behavior
- If FFprobe takes longer than `ffprobe_timeout`, analysis is cancelled
- File is processed using extension-based fallback
- Prevents hanging on corrupted or very large files

## Migration Guide

### From Extension-Only to Content Detection

1. **Update configuration** (optional - enabled by default):
   ```yaml
   scan:
     use_content_detection: true
   ```

2. **Test with known files**:
   ```bash
   corrupt-video-inspector scan /path/to/test/videos
   ```

3. **Optimize performance** if needed:
   ```yaml
   scan:
     extension_filter: [".mp4", ".mkv"]  # Common formats only
     ffprobe_timeout: 20                # Faster timeout
   ```

### Reverting to Extension-Only

```yaml
scan:
  use_content_detection: false
  extensions: [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"]
```