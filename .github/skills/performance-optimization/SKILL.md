---
name: performance-optimization
description: Skill for performance analysis and optimization in the Corrupt Video File Inspector project
---

# Performance Optimization Skill

This skill provides comprehensive guidance for analyzing and optimizing performance in the Corrupt Video File Inspector project.

## Required Tools

### Allowed Tools

**Profiling Tools (REQUIRED)**
- `cProfile` - CPU profiling
- `pstats` - Profile statistics analysis
- `memory_profiler` - Memory usage profiling
- `line_profiler` - Line-by-line profiling
- `py-spy` - Sampling profiler

**Benchmarking (REQUIRED)**
- `pytest-benchmark` - Performance testing
- `timeit` - Micro-benchmarking

**Monitoring (RECOMMENDED)**
- `psutil` - System resource monitoring
- `time` command - Basic timing

**What to Use:**
```bash
# ✅ DO: Use cProfile for CPU profiling
python -m cProfile -o profile.stats script.py
python -m pstats profile.stats

# ✅ DO: Use memory_profiler
python -m memory_profiler script.py

# ✅ DO: Use pytest-benchmark
pytest tests/ --benchmark-only

# ✅ DO: Use py-spy for sampling
py-spy record -o profile.svg -- python script.py
```

**What NOT to Use:**
```bash
# ❌ DON'T: Use commercial profilers without approval
# Intel VTune, JProfiler, etc.

# ❌ DON'T: Use experimental profilers
# Unvetted third-party tools
# Beta profiling software

# ❌ DON'T: Optimize without measuring
# Never guess at bottlenecks
# Always profile first
```

### Tool Usage Examples

**Example 1: Profile CPU Usage**
```python
import cProfile
import pstats

def profile_scan_directory(directory: Path) -> None:
    """Profile directory scanning."""
    profiler = cProfile.Profile()
    
    # Start profiling
    profiler.enable()
    
    # Code to profile
    scan_directory(directory)
    
    # Stop profiling
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
```

**Example 2: Memory Profiling**
```python
from memory_profiler import profile

@profile
def process_large_dataset():
    """Profile memory usage line by line."""
    videos = load_all_videos()  # Check memory here
    results = [scan(v) for v in videos]  # And here
    return aggregate_results(results)

# Run with: python -m memory_profiler script.py
```

**Example 3: Benchmark Performance**
```python
import pytest

@pytest.mark.benchmark(group="scanning")
def test_quick_scan_performance(benchmark, sample_video):
    """Benchmark quick scan mode."""
    result = benchmark(scan_video, sample_video, mode="quick")
    assert result.status in ["healthy", "corrupt"]

# Run: pytest tests/ --benchmark-only --benchmark-compare
```

**Example 4: Line-by-Line Profiling**
```python
from line_profiler import LineProfiler

def profile_function():
    """Profile specific function line by line."""
    profiler = LineProfiler()
    profiler.add_function(scan_video)
    profiler.enable()
    
    scan_video(sample_video)
    
    profiler.disable()
    profiler.print_stats()

# Or use decorator:
@profile  # When running kernprof
def scan_video(path: Path) -> ScanResult:
    """Video scanning with line profiling."""
    ...
```

**Example 5: Monitor System Resources**
```python
import psutil
import time

def monitor_scan_resources(directory: Path):
    """Monitor CPU and memory during scan."""
    process = psutil.Process()
    
    start_time = time.time()
    start_mem = process.memory_info().rss / 1024 / 1024  # MB
    
    # Run scan
    results = scan_directory(directory)
    
    end_time = time.time()
    end_mem = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"Time: {end_time - start_time:.2f}s")
    print(f"Memory: {end_mem - start_mem:.2f} MB increase")
    print(f"CPU: {process.cpu_percent()}%")
    
    return results
```

**Example 6: Performance Testing**
```bash
# Run benchmarks
pytest tests/ --benchmark-only

# Compare with baseline
pytest tests/ --benchmark-only --benchmark-compare=0001

# Save benchmark results
pytest tests/ --benchmark-only --benchmark-save=baseline

# Generate performance report
pytest tests/ --benchmark-only --benchmark-histogram
```

**Example 7: Flame Graph Profiling**
```bash
# Generate flame graph with py-spy
py-spy record -o profile.svg --format speedscope \
  -- python -m corrupt_video_inspector scan /videos

# View in browser
firefox profile.svg
```

## When to Use

Use this skill when:
- Application is running slowly
- Users report performance issues
- Processing large video libraries
- Optimizing resource usage
- Improving scalability
- Preventing performance regression

## Performance Optimization Principles

### Rule #1: Measure First

**Never optimize without data**
- Profile before optimizing
- Identify actual bottlenecks
- Measure impact of changes
- Use real-world workloads

**Premature Optimization is the Root of All Evil**
- Don't optimize for hypothetical issues
- Focus on proven bottlenecks
- Maintain code readability
- Optimize when needed, not before

### Rule #2: Focus on the Hot Path

**80/20 Rule**: 80% of time is spent in 20% of code
- Find the 20% that matters
- Optimize the hot path first
- Don't waste time on cold paths
- Use profiling to identify hot spots

### Rule #3: Verify Improvements

**Measure actual impact**
- Benchmark before and after
- Use statistical analysis
- Consider real-world scenarios
- Document improvements

## Profiling Techniques

### CPU Profiling with cProfile

```python
import cProfile
import pstats
from pathlib import Path

def profile_scan_directory(directory: Path) -> None:
    """Profile directory scanning."""
    profiler = cProfile.Profile()
    
    # Start profiling
    profiler.enable()
    
    # Code to profile
    scan_directory(directory)
    
    # Stop profiling
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')  # Sort by cumulative time
    stats.print_stats(20)  # Show top 20 functions
```

**Key Metrics**
- `ncalls`: Number of calls
- `tottime`: Total time in function (excluding subcalls)
- `cumtime`: Cumulative time (including subcalls)
- `percall`: Average time per call

### Memory Profiling

```python
from memory_profiler import profile

@profile
def process_large_dataset():
    """Profile memory usage line by line."""
    videos = load_all_videos()  # Memory spike here?
    results = [scan(v) for v in videos]  # Or here?
    return aggregate_results(results)

# Run with: python -m memory_profiler script.py
```

### Line Profiler for Detailed Analysis

```python
from line_profiler import LineProfiler

def profile_function():
    """Profile specific function line by line."""
    profiler = LineProfiler()
    profiler.add_function(scan_video)
    profiler.enable()
    
    scan_video(sample_video)
    
    profiler.disable()
    profiler.print_stats()
```

### Timing Specific Operations

```python
import time
from contextlib import contextmanager
from typing import Generator

@contextmanager
def timer(name: str) -> Generator[None, None, None]:
    """Context manager for timing operations."""
    start = time.perf_counter()
    yield
    end = time.perf_counter()
    print(f"{name} took {end - start:.4f}s")

# Usage
with timer("Video scanning"):
    results = scan_directory(video_dir)

with timer("Report generation"):
    report = generate_report(results)
```

## Common Performance Bottlenecks

### 1. Inefficient Loops

**Problem: Quadratic Complexity**
```python
# O(n²) - Very slow for large n
def find_duplicates_slow(videos: List[Path]) -> List[tuple]:
    """Slow duplicate detection."""
    duplicates = []
    for i, video1 in enumerate(videos):
        for video2 in videos[i+1:]:
            if are_duplicates(video1, video2):
                duplicates.append((video1, video2))
    return duplicates
```

**Solution: Use Sets or Dictionaries**
```python
# O(n) - Much faster
def find_duplicates_fast(videos: List[Path]) -> List[tuple]:
    """Fast duplicate detection using hashing."""
    seen = {}
    duplicates = []
    
    for video in videos:
        hash_val = compute_hash(video)
        if hash_val in seen:
            duplicates.append((seen[hash_val], video))
        else:
            seen[hash_val] = video
    
    return duplicates
```

### 2. Repeated Computations

**Problem: Computing Same Value Multiple Times**
```python
def process_videos(videos: List[Path]) -> List[Result]:
    """Recomputes config every iteration."""
    results = []
    for video in videos:
        config = load_config()  # Slow I/O repeated!
        result = scan_video(video, config)
        results.append(result)
    return results
```

**Solution: Cache or Compute Once**
```python
def process_videos(videos: List[Path]) -> List[Result]:
    """Load config once."""
    config = load_config()  # Load once
    results = []
    for video in videos:
        result = scan_video(video, config)
        results.append(result)
    return results

# Or use list comprehension
def process_videos(videos: List[Path]) -> List[Result]:
    """Even more efficient."""
    config = load_config()
    return [scan_video(video, config) for video in videos]
```

### 3. Memory Inefficiency

**Problem: Loading Everything into Memory**
```python
def scan_all_videos(directory: Path) -> List[ScanResult]:
    """Loads all videos at once - memory intensive."""
    videos = list(directory.rglob("*.mp4"))  # All in memory
    return [scan_video(v) for v in videos]
```

**Solution: Use Generators**
```python
def scan_all_videos(directory: Path) -> Iterator[ScanResult]:
    """Process videos one at a time."""
    for video in directory.rglob("*.mp4"):  # Generator
        yield scan_video(video)

# Or batch processing
def scan_all_videos_batched(
    directory: Path,
    batch_size: int = 100
) -> List[ScanResult]:
    """Process in batches."""
    videos = directory.rglob("*.mp4")
    results = []
    
    batch = []
    for video in videos:
        batch.append(video)
        if len(batch) >= batch_size:
            results.extend(process_batch(batch))
            batch = []
    
    if batch:  # Process remaining
        results.extend(process_batch(batch))
    
    return results
```

### 4. Sequential Processing

**Problem: Processing One at a Time**
```python
def scan_videos(videos: List[Path]) -> List[ScanResult]:
    """Sequential processing - slow."""
    return [scan_video(v) for v in videos]
```

**Solution: Parallel Processing**
```python
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from typing import List

def scan_videos_parallel(
    videos: List[Path],
    max_workers: int = None
) -> List[ScanResult]:
    """Parallel processing - much faster."""
    if max_workers is None:
        max_workers = min(cpu_count(), len(videos))
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_video = {
            executor.submit(scan_video, video): video
            for video in videos
        }
        
        # Collect results as they complete
        results = []
        for future in as_completed(future_to_video):
            video = future_to_video[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error scanning {video}: {e}")
        
        return results
```

### 5. Inefficient File I/O

**Problem: Reading File Multiple Times**
```python
def analyze_video(path: Path) -> Analysis:
    """Reads file metadata multiple times."""
    size = path.stat().st_size  # I/O operation
    modified = path.stat().st_mtime  # Another I/O
    created = path.stat().st_ctime  # And another
    return Analysis(size, modified, created)
```

**Solution: Read Once**
```python
def analyze_video(path: Path) -> Analysis:
    """Read metadata once."""
    stat = path.stat()  # Single I/O operation
    return Analysis(
        stat.st_size,
        stat.st_mtime,
        stat.st_ctime
    )
```

### 6. String Concatenation in Loops

**Problem: Slow String Building**
```python
def build_report(results: List[ScanResult]) -> str:
    """Slow string concatenation."""
    report = ""
    for result in results:
        report += f"{result.path}: {result.status}\n"  # Slow!
    return report
```

**Solution: Use join() or StringIO**
```python
def build_report(results: List[ScanResult]) -> str:
    """Fast string building."""
    lines = [
        f"{result.path}: {result.status}"
        for result in results
    ]
    return "\n".join(lines)

# Or for very large reports
from io import StringIO

def build_report_large(results: List[ScanResult]) -> str:
    """Efficient for large reports."""
    buffer = StringIO()
    for result in results:
        buffer.write(f"{result.path}: {result.status}\n")
    return buffer.getvalue()
```

## Python Performance Patterns

### Use Built-in Functions

Built-in functions are implemented in C and much faster:

```python
# Slower
def sum_list(numbers: List[int]) -> int:
    total = 0
    for num in numbers:
        total += num
    return total

# Faster
def sum_list(numbers: List[int]) -> int:
    return sum(numbers)  # Built-in is faster
```

### List Comprehensions vs. Loops

```python
# Slower
result = []
for item in items:
    if item.is_valid():
        result.append(item.process())

# Faster (and more Pythonic)
result = [
    item.process()
    for item in items
    if item.is_valid()
]
```

### Use Local Variables

```python
# Slower: Repeated attribute lookup
def process_videos(self, videos: List[Path]) -> List[Result]:
    return [
        self.scanner.scan(video)  # Attribute lookup each time
        for video in videos
    ]

# Faster: Store in local variable
def process_videos(self, videos: List[Path]) -> List[Result]:
    scan = self.scanner.scan  # Local variable
    return [scan(video) for video in videos]
```

### Avoid Function Call Overhead

```python
# Slower: Function call overhead
def is_valid_extension(path: Path) -> bool:
    return path.suffix in [".mp4", ".mkv", ".avi"]

files = [f for f in files if is_valid_extension(f)]

# Faster: Inline simple operations
valid_extensions = {".mp4", ".mkv", ".avi"}
files = [f for f in files if f.suffix in valid_extensions]
```

### Use Sets for Membership Testing

```python
# Slower: O(n) lookup in list
valid_extensions = [".mp4", ".mkv", ".avi", ".mov", ".wmv"]
if file.suffix in valid_extensions:  # Linear search
    ...

# Faster: O(1) lookup in set
valid_extensions = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
if file.suffix in valid_extensions:  # Hash lookup
    ...
```

## Caching Strategies

### LRU Cache for Function Results

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_video_metadata(path: Path) -> Metadata:
    """Cache metadata for frequently accessed videos."""
    return extract_metadata(path)  # Expensive operation
```

### Class-Level Caching

```python
class VideoScanner:
    """Scanner with result caching."""
    
    def __init__(self):
        self._cache: Dict[Path, ScanResult] = {}
    
    def scan(self, path: Path, use_cache: bool = True) -> ScanResult:
        """Scan with optional caching."""
        if use_cache and path in self._cache:
            return self._cache[path]
        
        result = self._perform_scan(path)
        
        if use_cache:
            self._cache[path] = result
        
        return result
```

### Time-Based Cache Expiration

```python
from datetime import datetime, timedelta
from typing import Optional, Tuple

class CachedScanner:
    """Scanner with time-based cache expiration."""
    
    def __init__(self, cache_ttl: timedelta = timedelta(hours=1)):
        self.cache_ttl = cache_ttl
        self._cache: Dict[Path, Tuple[ScanResult, datetime]] = {}
    
    def scan(self, path: Path) -> ScanResult:
        """Scan with cache expiration."""
        now = datetime.now()
        
        if path in self._cache:
            result, cached_at = self._cache[path]
            if now - cached_at < self.cache_ttl:
                return result
        
        result = self._perform_scan(path)
        self._cache[path] = (result, now)
        return result
```

## Database Optimization

### Batch Database Operations

```python
# Slower: Individual inserts
def save_results_slow(results: List[ScanResult]) -> None:
    """Slow individual inserts."""
    for result in results:
        db.execute(
            "INSERT INTO scans VALUES (?, ?, ?)",
            (result.path, result.status, result.timestamp)
        )
        db.commit()  # Commit after each insert

# Faster: Batch insert
def save_results_fast(results: List[ScanResult]) -> None:
    """Fast batch insert."""
    data = [
        (r.path, r.status, r.timestamp)
        for r in results
    ]
    db.executemany(
        "INSERT INTO scans VALUES (?, ?, ?)",
        data
    )
    db.commit()  # Single commit
```

### Use Indexes

```sql
-- Add index for common queries
CREATE INDEX idx_scans_path ON scans(path);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_timestamp ON scans(timestamp);
```

### Connection Pooling

```python
from contextlib import contextmanager
import sqlite3

class DatabasePool:
    """Simple connection pool."""
    
    def __init__(self, db_path: Path, pool_size: int = 5):
        self.db_path = db_path
        self.pool = [
            sqlite3.connect(db_path)
            for _ in range(pool_size)
        ]
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        conn = self.pool.pop()
        try:
            yield conn
        finally:
            self.pool.append(conn)
```

## Benchmarking

### Using pytest-benchmark

```python
import pytest

@pytest.mark.benchmark(group="scanning")
def test_quick_scan_performance(benchmark, sample_video):
    """Benchmark quick scan mode."""
    result = benchmark(scan_video, sample_video, mode="quick")
    assert result.status in ["healthy", "corrupt"]

@pytest.mark.benchmark(group="scanning")
def test_deep_scan_performance(benchmark, sample_video):
    """Benchmark deep scan mode."""
    result = benchmark(scan_video, sample_video, mode="deep")
    assert result.status in ["healthy", "corrupt"]

# Run benchmarks
# pytest tests/ --benchmark-only
# pytest tests/ --benchmark-compare
```

### Custom Benchmarking

```python
import time
from statistics import mean, stdev

def benchmark_function(
    func,
    *args,
    iterations: int = 100,
    **kwargs
):
    """Benchmark a function."""
    times = []
    
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)
    
    return {
        "mean": mean(times),
        "stdev": stdev(times),
        "min": min(times),
        "max": max(times)
    }

# Usage
stats = benchmark_function(scan_video, sample_path, iterations=50)
print(f"Mean: {stats['mean']:.4f}s ± {stats['stdev']:.4f}s")
```

## Performance Testing

### Regression Tests

```python
@pytest.mark.performance
def test_scan_performance_regression(sample_videos):
    """Ensure scan performance doesn't regress."""
    start = time.perf_counter()
    results = scan_videos(sample_videos)
    elapsed = time.perf_counter() - start
    
    # Should complete within time limit
    max_time = 10.0  # seconds
    assert elapsed < max_time, f"Scan took {elapsed:.2f}s (max: {max_time}s)"
    assert len(results) == len(sample_videos)
```

### Load Testing

```python
def test_scan_large_library():
    """Test performance with large video library."""
    # Create test videos
    video_dir = create_test_videos(count=1000)
    
    start = time.perf_counter()
    results = scan_directory(video_dir, parallel=True)
    elapsed = time.perf_counter() - start
    
    throughput = len(results) / elapsed
    print(f"Throughput: {throughput:.2f} videos/second")
    
    # Verify acceptable throughput
    assert throughput > 10  # At least 10 videos/second
```

## Optimization Checklist

### Before Optimization
- [ ] Profile to identify bottlenecks
- [ ] Measure current performance
- [ ] Set optimization goals
- [ ] Ensure tests pass
- [ ] Document baseline performance

### During Optimization
- [ ] Focus on hot paths
- [ ] Make incremental changes
- [ ] Maintain code readability
- [ ] Keep changes isolated
- [ ] Add performance tests

### After Optimization
- [ ] Benchmark improvements
- [ ] Verify correctness (all tests pass)
- [ ] Document optimization
- [ ] Update performance tests
- [ ] Review code quality
- [ ] Measure real-world impact

## Common Mistakes

### 1. Optimizing Without Measuring
- Always profile first
- Don't guess where the bottleneck is
- Measure actual impact

### 2. Micro-Optimizations
- Don't optimize cold paths
- Focus on big wins first
- Readability > tiny speed gains

### 3. Breaking Functionality
- Always run tests after optimization
- Verify behavior is preserved
- Check edge cases

### 4. Over-Engineering
- Simple solutions often faster
- Don't add complexity prematurely
- Balance performance and maintainability

## Tools Reference

### Profiling Tools
```bash
# CPU profiling
python -m cProfile -o profile.stats script.py
python -m pstats profile.stats

# Memory profiling
python -m memory_profiler script.py

# Line profiling
kernprof -l script.py
python -m line_profiler script.py.lprof
```

### Benchmarking Tools
```bash
# pytest-benchmark
pytest tests/ --benchmark-only
pytest tests/ --benchmark-compare

# timeit module
python -m timeit -s "setup code" "code to time"
```

### Analysis Tools
```bash
# Find slow code
pyinstrument script.py

# Memory leaks
pympler script.py

# Code complexity
radon cc src/ -a -nc
```

## References

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [High Performance Python](https://www.oreilly.com/library/view/high-performance-python/9781492055013/)
- [profiling](https://docs.python.org/3/library/profile.html)
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
