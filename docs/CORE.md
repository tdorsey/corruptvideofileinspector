# Core Module Documentation

The Core module (`src/core/`) contains the main business logic for video file analysis, corruption detection, and result reporting. It provides the fundamental algorithms and data structures that power the Corrupt Video Inspector.

## Architecture

```
src/core/
├── scanner.py              # Video file scanning orchestration
├── inspector.py            # Individual file corruption analysis
├── reporter.py             # Report generation in multiple formats
├── watchlist.py            # Trakt.tv watchlist integration
├── utils.py                # Core utility functions
├── exceptions.py           # Custom exception definitions
├── models/                 # Data models and schemas
│   ├── scanning/           # Scan-related models
│   ├── inspection/         # File inspection models
│   ├── reporting/          # Report structure models
│   └── watchlist/          # Watchlist sync models
└── errors/
    └── errors.py           # Error handling utilities
```

## Components

### Scanner (`scanner.py`)

The main orchestration component responsible for:
- **Directory traversal**: Recursive file discovery with extension filtering
- **Parallel processing**: Multi-threaded file analysis using configurable worker pools
- **Resume capability**: Write-Ahead Logging (WAL) for interrupted scan recovery
- **Progress tracking**: Real-time progress reporting with signal handling
- **Mode management**: Quick, deep, and hybrid scanning strategies

#### Key Features:
- **Scan Modes**:
  - `quick`: Fast 1-minute timeout per file
  - `deep`: Thorough 15-minute timeout per file  
  - `hybrid`: Quick scan first, then deep scan suspicious files
- **Resume functionality**: Automatically resumes interrupted scans
- **Signal handling**: Graceful shutdown on SIGINT/SIGTERM
- **Progress reporting**: Real-time status updates

### Inspector (`inspector.py`)

Handles individual file corruption analysis:
- **FFmpeg integration**: Leverages FFmpeg for video stream analysis
- **Pattern detection**: Advanced corruption pattern matching
- **Confidence scoring**: Assigns corruption probability scores
- **Timeout management**: Configurable analysis timeouts
- **Error classification**: Categorizes different types of corruption

#### Analysis Process:
1. **Stream validation**: Check basic video stream integrity
2. **Frame analysis**: Examine individual frames for corruption indicators
3. **Pattern matching**: Look for known corruption signatures
4. **Confidence calculation**: Generate probability score (0.0-1.0)
5. **Result aggregation**: Combine multiple analysis results

### Reporter (`reporter.py`)

Generates comprehensive reports in multiple formats:
- **Format support**: JSON, CSV, YAML, and plain text
- **Analytics**: File size statistics, scan performance metrics
- **Filtering**: Include/exclude healthy files, confidence thresholds
- **Sorting**: Multiple sort criteria (path, size, corruption, confidence)
- **Grouping**: Directory-based result organization

#### Report Types:
- **Summary reports**: High-level statistics and metrics
- **Detailed reports**: Per-file analysis results
- **Analytics reports**: Performance and distribution analysis
- **Export formats**: Machine-readable and human-readable options

### Watchlist (`watchlist.py`)

Integrates with Trakt.tv for media collection syncing:
- **Filename parsing**: Intelligent extraction of movie/TV show metadata
- **API integration**: Trakt.tv API v2 communication
- **Match resolution**: Handles multiple search results
- **Batch operations**: Efficient bulk watchlist updates
- **Error handling**: Robust API error recovery

#### Capabilities:
- **Media detection**: Automatic movie vs TV show classification
- **Metadata extraction**: Title, year, season/episode parsing
- **Search matching**: Fuzzy matching with confidence scoring
- **Interactive mode**: Manual selection for ambiguous results

### Models

The models directory contains data structures and schemas:

#### Scanning Models
- `ScanRequest`: Input parameters for scan operations
- `ScanResult`: Individual file analysis results
- `ScanSummary`: Aggregate scan statistics

#### Inspection Models  
- `FileInspectionResult`: Detailed file analysis data
- `CorruptionIndicator`: Specific corruption pattern information
- `ConfidenceScore`: Corruption probability assessment

#### Reporting Models
- `ScanReport`: Complete report structure
- `ReportConfiguration`: Report generation settings
- `ReportMetadata`: Report generation metadata

#### Watchlist Models
- `MediaItem`: Parsed media information
- `WatchlistSyncResult`: Sync operation results
- `TraktMatch`: Search result matching data

## Key Algorithms

### Hybrid Scanning Strategy

The hybrid mode combines speed and thoroughness:

```python
def hybrid_scan(files):
    # Phase 1: Quick scan all files
    quick_results = quick_scan_all(files)
    
    # Phase 2: Deep scan suspicious files
    suspicious = [f for f in quick_results if f.confidence > 0.3]
    deep_results = deep_scan_files(suspicious)
    
    # Merge results with deep scan taking precedence
    return merge_results(quick_results, deep_results)
```

### Corruption Pattern Detection

Advanced pattern matching for corruption indicators:

```python
def detect_corruption_patterns(ffmpeg_output):
    patterns = [
        'Stream contains DTS packets',
        'Invalid NAL unit size',
        'Frame corrupt or truncated',
        'Error while decoding stream'
    ]
    
    confidence = 0.0
    for pattern in patterns:
        if pattern in ffmpeg_output:
            confidence += get_pattern_weight(pattern)
    
    return min(confidence, 1.0)
```

### Media Filename Parsing

Intelligent extraction of media metadata:

```python
def parse_filename(filename):
    # Extract year pattern
    year_match = re.search(r'\b(19|20)\d{2}\b', filename)
    
    # Extract season/episode for TV shows
    episode_match = re.search(r'[Ss](\d+)[Ee](\d+)', filename)
    
    # Clean title by removing common artifacts
    title = clean_title(filename, year_match, episode_match)
    
    return MediaItem(title=title, year=year, season=season, episode=episode)
```

## Error Handling

The core module implements comprehensive error handling:

### Exception Hierarchy
- `CoreException`: Base exception for core module
- `ScanException`: Scanning operation errors
- `InspectionException`: File analysis errors  
- `ReportException`: Report generation errors
- `WatchlistException`: Trakt integration errors

### Recovery Strategies
- **Timeout handling**: Graceful timeout with partial results
- **File access errors**: Skip inaccessible files, continue processing
- **API failures**: Retry with exponential backoff
- **Corruption detection**: Fallback to alternate analysis methods

## Performance Considerations

### Optimization Strategies
- **Parallel processing**: Configurable worker thread pools
- **Memory management**: Streaming for large file sets
- **Caching**: FFmpeg binary location and metadata caching
- **Early termination**: Stop analysis on clear corruption indicators

### Scalability
- **Large directories**: Efficient directory traversal algorithms
- **Memory usage**: Bounded memory consumption regardless of file count
- **Progress tracking**: Minimal overhead progress reporting
- **Resume capability**: Disk-based state persistence

## Configuration Integration

Core components integrate with the configuration system:

```python
class Scanner:
    def __init__(self, config: AppConfig):
        self.max_workers = config.processing.max_workers
        self.default_mode = config.processing.default_mode
        self.quick_timeout = config.ffmpeg.quick_timeout
        self.deep_timeout = config.ffmpeg.deep_timeout
```

## Testing Strategy

Core module testing includes:
- **Unit tests**: Individual component testing with mocks
- **Integration tests**: Cross-component interaction testing
- **Performance tests**: Load and stress testing
- **Regression tests**: Corruption detection accuracy validation

## Dependencies

- **FFmpeg**: External video analysis tool
- **Threading**: Python concurrent.futures for parallelization  
- **Requests**: HTTP client for Trakt API integration
- **PyYAML**: Configuration and report serialization
- **Rich**: Progress display and formatting