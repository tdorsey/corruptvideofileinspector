# FFprobe Results Tracking Implementation Summary

This document summarizes the implementation of the probe-before-scan workflow feature as requested in issue #170.

## Feature Overview

The implementation adds comprehensive FFprobe analysis and caching to enforce a probe-before-scan workflow, ensuring that corruption scanning only occurs on files that have successfully completed FFprobe analysis.

## Key Components Implemented

### 1. Core Models (`src/core/models/probe.py`)
- **ProbeResult**: Tracks FFprobe analysis results with metadata
- **StreamInfo**: Represents individual media streams (video/audio/subtitle)
- **FormatInfo**: Container format information from FFprobe
- **ScanPrerequisites**: Helper class to validate scan eligibility

### 2. FFprobe Client (`src/ffmpeg/ffprobe_client.py`)
- Executes FFprobe with JSON output for metadata extraction
- Parses stream and format information
- Handles timeouts and errors gracefully
- Validates FFprobe installation and capabilities

### 3. Probe Result Cache (`src/core/probe_cache.py`)
- Persistent JSON-based caching with expiration
- Thread-safe operations with file locking
- Automatic cleanup of expired entries
- Statistics and management functions

### 4. Configuration Extensions (`src/config/config.py`)
- `probe_timeout`: FFprobe operation timeout
- `enable_probe_cache`: Toggle persistent caching
- `probe_cache_max_age_hours`: Cache expiration time
- `require_probe_before_scan`: Enforce probe workflow

### 5. Scanner Integration (`src/core/scanner.py`)
- Probe phase before corruption scanning
- Eligibility checking based on probe results
- Integration with existing scan workflows
- Probe result inclusion in scan results

### 6. FFmpeg Client Updates (`src/ffmpeg/ffmpeg_client.py`)
- All inspection methods accept optional probe results
- Probe information included in ScanResult objects
- Enhanced reporting with metadata

### 7. CLI Integration (`src/cli/commands.py`)
- `test-ffprobe` command for testing probe functionality
- Enhanced scan results with probe information

## Workflow Implementation

### Phase 1: File Discovery
Scanner discovers video files using existing logic with extension filtering.

### Phase 2: Probe Analysis (New)
```python
# For each discovered file:
if self.config.ffmpeg.require_probe_before_scan:
    probe_result = self._probe_file(video_file)
    can_scan, reason = self._can_scan_file(video_file, probe_result)
    if can_scan:
        eligible_files.append(video_file)
    else:
        logger.info(f"Skipping {video_file.path}: {reason}")
```

### Phase 3: Corruption Scanning
Only eligible files undergo corruption analysis:
```python
result = ffmpeg_client.inspect_quick(video_file, probe_result)
# Probe result is included in the ScanResult
```

## Data Structures

### ProbeResult Example
```python
ProbeResult(
    file_path=Path("/video.mp4"),
    success=True,
    streams=[
        StreamInfo(index=0, codec_type=StreamType.VIDEO, codec_name="h264"),
        StreamInfo(index=1, codec_type=StreamType.AUDIO, codec_name="aac")
    ],
    format_info=FormatInfo(format_name="mov,mp4", duration=120.5),
    duration=120.5,
    file_size=50000000
)
```

### Enhanced ScanResult
```json
{
  "filename": "/video.mp4",
  "is_corrupt": false,
  "status": "HEALTHY",
  "probe_success": true,
  "has_video_streams": true,
  "probe_duration": 120.5,
  "probe_summary": "1 video, 1 audio streams, 120.5s"
}
```

## Benefits Achieved

### 1. Reliable Workflow
- ✅ Only validated video files undergo corruption analysis
- ✅ Clear separation between probe failures and scan failures
- ✅ Graceful handling of non-video files

### 2. Performance Optimization
- ✅ Cached probe results avoid redundant operations
- ✅ Early rejection of ineligible files saves resources
- ✅ Configurable cache expiration and cleanup

### 3. Enhanced Metadata
- ✅ Rich file information from FFprobe preserved
- ✅ Stream details and format information available
- ✅ Duration and codec information for reporting

### 4. Process Integrity
- ✅ Guaranteed file validation before scanning
- ✅ Configurable enforcement of probe requirements
- ✅ Backward compatibility with existing workflows

### 5. Audit Trail
- ✅ Probe results maintained for troubleshooting
- ✅ Clear logging of eligibility decisions
- ✅ Statistics and cache management

### 6. Incremental Processing
- ✅ Resume operations without re-probing files
- ✅ Cache persistence across application runs
- ✅ File modification time checking

## Testing Implementation

### Unit Tests
- **test_probe_models.py**: ProbeResult, StreamInfo, FormatInfo validation
- **test_ffprobe_client.py**: FFprobe execution and result parsing
- **test_probe_cache.py**: Caching, persistence, and expiration
- **test_probe_integration.py**: Workflow integration concepts

### CLI Testing
- **test-ffprobe command**: Validate FFprobe functionality on specific files
- **Enhanced scan output**: Probe information in all scan results

## Configuration Examples

### Enable Probe Workflow
```yaml
ffmpeg:
  require_probe_before_scan: true
  enable_probe_cache: true
  probe_timeout: 15
  probe_cache_max_age_hours: 24.0
```

### Disable for Legacy Behavior
```yaml
ffmpeg:
  require_probe_before_scan: false
```

## Backward Compatibility

- ✅ Feature is optional and configurable
- ✅ Existing scan workflows unchanged when disabled
- ✅ No breaking changes to CLI or API
- ✅ ScanResult model extended with optional fields

## Future Enhancements

The implementation provides a foundation for:
- Database storage for probe cache
- Advanced stream validation rules
- Media information extraction pipelines
- Integration with external metadata services

## Files Created/Modified

### New Files
- `src/core/models/probe.py`
- `src/ffmpeg/ffprobe_client.py`
- `src/core/probe_cache.py`
- `tests/unit/test_probe_models.py`
- `tests/unit/test_ffprobe_client.py`
- `tests/unit/test_probe_cache.py`
- `tests/unit/test_probe_integration.py`
- `docs/PROBE.md`
- `config.probe.yaml`

### Modified Files
- `src/config/config.py` - Added probe configuration
- `src/core/models/scanning/__init__.py` - Added probe_result to ScanResult
- `src/core/scanner.py` - Integrated probe workflow
- `src/ffmpeg/ffmpeg_client.py` - Added probe result parameters
- `src/cli/commands.py` - Added test-ffprobe command
- `docs/FFMPEG.md` - Updated to reference probe functionality

## Implementation Quality

- ✅ Type annotations throughout
- ✅ Comprehensive error handling
- ✅ Thread-safe cache operations
- ✅ Configurable timeouts and behavior
- ✅ Extensive logging and debugging support
- ✅ Unit test coverage for all components
- ✅ Documentation and examples provided

This implementation fully satisfies the requirements specified in issue #170 for tracking FFprobe results and enforcing a probe-before-scan workflow.