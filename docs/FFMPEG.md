# FFmpeg Integration Documentation

The FFmpeg integration module (`src/ffmpeg/`) provides the video analysis capabilities that power the corruption detection system. It manages FFmpeg execution, output parsing, and corruption pattern analysis.

## Architecture

```
src/ffmpeg/
├── ffmpeg_client.py        # FFmpeg command execution and management
└── corruption_detector.py  # Corruption pattern analysis and detection
```

## Components

### FFmpeg Client (`ffmpeg_client.py`)

Manages FFmpeg binary execution and communication:

#### Key Features:
- **Binary detection**: Automatic FFmpeg binary location discovery
- **Command construction**: Safe command-line argument building
- **Timeout management**: Configurable execution timeouts
- **Output capture**: Real-time stdout/stderr capture
- **Process management**: Clean process lifecycle handling
- **Error handling**: Robust failure recovery and reporting

#### Core Functionality:

```python
class FFmpegClient:
    def __init__(self, config: FFmpegConfig):
        self.binary_path = self._detect_ffmpeg_binary()
        self.quick_timeout = config.quick_timeout
        self.deep_timeout = config.deep_timeout
    
    def analyze_video(self, file_path: Path, timeout: int) -> FFmpegResult:
        """Execute FFmpeg analysis on a video file"""
        # Construct safe command
        # Execute with timeout
        # Parse output
        # Return structured result
```

### Corruption Detector (`corruption_detector.py`)

Analyzes FFmpeg output to identify corruption patterns:

#### Detection Strategies:
- **Pattern matching**: Known corruption error signatures
- **Statistical analysis**: Frame error rate calculation
- **Stream validation**: Video stream integrity checks
- **Confidence scoring**: Weighted corruption probability

#### Core Algorithm:

```python
class CorruptionDetector:
    def detect_corruption(self, ffmpeg_output: str) -> CorruptionResult:
        """Analyze FFmpeg output for corruption indicators"""
        confidence = 0.0
        indicators = []
        
        # Check for critical errors
        confidence += self._check_critical_patterns(ffmpeg_output)
        
        # Analyze frame errors
        confidence += self._analyze_frame_errors(ffmpeg_output)
        
        # Check stream integrity
        confidence += self._validate_streams(ffmpeg_output)
        
        return CorruptionResult(
            is_corrupt=confidence > self.threshold,
            confidence=min(confidence, 1.0),
            indicators=indicators
        )
```

## FFmpeg Command Strategies

### Quick Analysis
Fast corruption detection with minimal processing:

```bash
ffmpeg -v error -i video.mp4 -f null - -t 60
```

**Purpose**: 
- Basic stream validation
- Detect obvious corruption quickly
- Minimize resource usage

**Timeout**: 60 seconds (configurable)

### Deep Analysis
Comprehensive corruption detection with full file analysis:

```bash
ffmpeg -v error -i video.mp4 -f null - -stats
```

**Purpose**:
- Complete file analysis
- Detect subtle corruption patterns
- Maximum accuracy

**Timeout**: 900 seconds (configurable)

## Corruption Patterns

### Critical Error Patterns

High-confidence corruption indicators:

```python
CRITICAL_PATTERNS = {
    'Stream contains DTS packets': 0.9,
    'Invalid NAL unit size': 0.8,
    'Frame corrupt or truncated': 0.9,
    'Error while decoding stream': 0.7,
    'Invalid bitstream format': 0.8,
    'Missing reference picture': 0.6,
    'Corrupt input packet': 0.9
}
```

### Warning Patterns

Medium-confidence indicators requiring further analysis:

```python
WARNING_PATTERNS = {
    'Non-monotonous DTS': 0.4,
    'Timestamp discontinuity': 0.3,
    'Frame skipped': 0.2,
    'Buffer underflow': 0.3,
    'Invalid frame size': 0.5
}
```

### Statistical Thresholds

Frame error rate analysis:

```python
def analyze_frame_errors(self, output: str) -> float:
    total_frames = self._extract_frame_count(output)
    error_frames = self._count_error_frames(output)
    
    if total_frames == 0:
        return 0.0
    
    error_rate = error_frames / total_frames
    
    # Convert error rate to confidence score
    if error_rate > 0.1:    # >10% error rate
        return 0.8
    elif error_rate > 0.05: # >5% error rate  
        return 0.6
    elif error_rate > 0.01: # >1% error rate
        return 0.3
    else:
        return 0.0
```

## Configuration

FFmpeg integration is configured through the main configuration system:

```yaml
ffmpeg:
  command: null                 # Auto-detect if not specified
  quick_timeout: 60            # Quick scan timeout in seconds
  deep_timeout: 900            # Deep scan timeout in seconds
  detection_threshold: 0.5     # Corruption confidence threshold
```

### Environment Variables

```bash
# Override FFmpeg binary location
export CVI_FFMPEG_COMMAND=/usr/local/bin/ffmpeg

# Adjust timeouts
export CVI_FFMPEG_QUICK_TIMEOUT=30
export CVI_FFMPEG_DEEP_TIMEOUT=1800
```

## Binary Detection

Automatic FFmpeg binary discovery:

```python
def _detect_ffmpeg_binary(self) -> str:
    """Locate FFmpeg binary using multiple strategies"""
    
    # 1. Check configuration override
    if self.config.command:
        return self.config.command
    
    # 2. Check environment variable
    if env_path := os.getenv('CVI_FFMPEG_COMMAND'):
        return env_path
    
    # 3. Search system PATH
    if which_path := shutil.which('ffmpeg'):
        return which_path
    
    # 4. Check common installation locations
    common_paths = [
        '/usr/bin/ffmpeg',
        '/usr/local/bin/ffmpeg',
        '/opt/homebrew/bin/ffmpeg'
    ]
    
    for path in common_paths:
        if Path(path).exists():
            return path
    
    raise FFmpegNotFoundError("FFmpeg binary not found")
```

## Error Handling

### FFmpeg Execution Errors

```python
class FFmpegException(Exception):
    """Base exception for FFmpeg-related errors"""
    pass

class FFmpegNotFoundError(FFmpegException):
    """FFmpeg binary not found"""
    pass

class FFmpegTimeoutError(FFmpegException):
    """FFmpeg execution timeout"""
    pass

class FFmpegExecutionError(FFmpegException):
    """FFmpeg execution failed"""
    pass
```

### Recovery Strategies

1. **Binary not found**: Provide clear installation instructions
2. **Execution timeout**: Return partial results with timeout indicator
3. **Command failure**: Retry with reduced parameters
4. **Output parsing errors**: Use fallback detection methods

## Performance Optimization

### Process Management
- **Resource limits**: Memory and CPU usage constraints
- **Process cleanup**: Ensure no orphaned processes
- **Concurrent execution**: Thread-safe FFmpeg client pool
- **Output buffering**: Efficient stdout/stderr handling

### Caching
- **Binary location**: Cache FFmpeg binary path
- **Command templates**: Pre-built command structures  
- **Pattern compilation**: Compiled regex patterns
- **Metadata extraction**: Cache file metadata when possible

## Testing

### Unit Tests
- Mock FFmpeg execution for deterministic testing
- Test corruption pattern detection with known samples
- Validate command construction and argument safety
- Error handling and recovery testing

### Integration Tests
- Real FFmpeg execution with test video files
- Corruption detection accuracy validation
- Performance benchmarking
- Cross-platform compatibility testing

### Test Fixtures
```
tests/fixtures/test-videos/
├── corrupt/              # Known corrupt video files
│   ├── frame_corruption.mp4
│   ├── stream_error.mkv
│   └── truncated.avi
└── healthy/              # Known healthy video files
    ├── sample.mp4
    ├── test_video.mkv
    └── reference.avi
```

## Docker Integration

FFmpeg in containerized environments:

```dockerfile
# Install FFmpeg in Docker image
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Verify installation
RUN ffmpeg -version
```

### Volume Considerations
- **Input files**: Mount video directories as read-only volumes
- **Output**: Ensure write permissions for reports
- **Temporary files**: Handle FFmpeg temp file creation

## Troubleshooting

### Common Issues

1. **FFmpeg not found**:
   ```bash
   # Install FFmpeg
   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # macOS with Homebrew
   brew install ffmpeg
   
   # Verify installation
   ffmpeg -version
   ```

2. **Permission denied**:
   - Check file permissions on video files
   - Ensure FFmpeg binary is executable
   - Verify write permissions for output directory

3. **Timeout issues**:
   - Adjust timeout values for large files
   - Consider hybrid mode for balance
   - Check system resources (CPU, memory)

4. **Incorrect corruption detection**:
   - Review detection threshold settings
   - Examine FFmpeg output manually
   - Report false positives for pattern improvement

### Debug Mode

Enable verbose FFmpeg output for troubleshooting:

```python
# Debug configuration
debug_config = FFmpegConfig(
    command='/usr/bin/ffmpeg',
    quick_timeout=120,
    deep_timeout=1800,
    verbose=True,  # Enable debug output
    save_logs=True  # Save FFmpeg logs
)
```

## Dependencies

- **FFmpeg**: External binary dependency (version 4.0+ recommended)
- **subprocess**: Python standard library for process execution
- **threading**: Timeout and concurrent execution management
- **pathlib**: Cross-platform path handling
- **re**: Regular expression pattern matching