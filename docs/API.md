# API Documentation

The Corrupt Video Inspector web API provides RESTful endpoints and WebSocket support for managing video corruption scans through a web interface.

## Overview

- **Technology**: FastAPI (Python 3.13+)
- **Base URL**: `http://localhost:8000/api`
- **WebSocket**: `ws://localhost:8000/ws`
- **Data Format**: JSON
- **Authentication**: None (MVP - can be added later)

## Running the API Server

### Development Mode

```bash
# Direct execution
python api_server.py

# Using Make
make api-dev
```

The API server will start on `http://localhost:8000`.

### Docker Mode

```bash
# Build and run with Docker Compose
make web-docker-build
make web-docker-up
```

## API Endpoints

### Health Check

Check API server status and FFmpeg availability.

**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "ffmpeg_available": true
}
```

**Status Codes**:
- `200 OK`: Service is healthy
- `500 Internal Server Error`: Service is unhealthy

---

### Start New Scan

Initiate a new video corruption scan.

**Endpoint**: `POST /api/scans`

**Request Body**:
```json
{
  "directory": "/app/videos",
  "mode": "quick",
  "recursive": true,
  "max_workers": 8
}
```

**Parameters**:
- `directory` (string, required): Absolute path to video directory
- `mode` (string, required): Scan mode - `"quick"`, `"deep"`, or `"hybrid"`
- `recursive` (boolean, optional): Scan subdirectories (default: `true`)
- `max_workers` (integer, optional): Number of parallel workers (1-32, default: 8)

**Response**:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Scan started successfully"
}
```

**Status Codes**:
- `200 OK`: Scan started
- `400 Bad Request`: Invalid directory or parameters
- `500 Internal Server Error`: Failed to start scan

---

### Get Scan Status

Retrieve current status and progress of a scan.

**Endpoint**: `GET /api/scans/{scan_id}`

**Response**:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "directory": "/app/videos",
  "mode": "quick",
  "progress": {
    "processed_count": 42,
    "total_files": 100,
    "current_file": "/app/videos/movie.mp4",
    "healthy_count": 38,
    "corrupt_count": 4,
    "suspicious_count": 0,
    "progress_percentage": 42.0,
    "elapsed_time": 125.5,
    "estimated_remaining_time": 173.2,
    "processing_rate": 0.33,
    "phase": "quick",
    "scan_mode": "quick"
  },
  "results": null,
  "error": null
}
```

**Scan Statuses**:
- `pending`: Scan queued but not started
- `running`: Scan in progress
- `completed`: Scan finished successfully
- `failed`: Scan encountered an error
- `cancelled`: Scan was cancelled by user

**Status Codes**:
- `200 OK`: Status retrieved
- `404 Not Found`: Scan ID not found

---

### Get Scan Results

Retrieve detailed results of a completed scan.

**Endpoint**: `GET /api/scans/{scan_id}/results`

**Response**:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [],
  "summary": {
    "directory": "/app/videos",
    "total_files": 100,
    "processed_files": 100,
    "corrupt_files": 5,
    "healthy_files": 95,
    "scan_mode": "quick",
    "scan_time": 298.7,
    "deep_scans_needed": 0,
    "deep_scans_completed": 0,
    "was_resumed": false
  }
}
```

**Note**: Individual file results (`results` array) are not currently implemented and return an empty array. Only summary statistics are available.

**Status Codes**:
- `200 OK`: Results retrieved
- `400 Bad Request`: Scan not completed
- `404 Not Found`: Scan ID not found or results not available

---

### Cancel Scan

Cancel a running scan.

**Endpoint**: `DELETE /api/scans/{scan_id}`

**Response**:
```json
{
  "message": "Scan cancelled successfully"
}
```

**Status Codes**:
- `200 OK`: Scan cancelled
- `400 Bad Request`: Cannot cancel scan in current state
- `404 Not Found`: Scan ID not found

---

### Get Database Statistics

Retrieve database statistics (placeholder for future implementation).

**Endpoint**: `GET /api/database/stats`

**Response**:
```json
{
  "total_files": 0,
  "healthy_files": 0,
  "corrupt_files": 0,
  "suspicious_files": 0,
  "last_scan_time": null
}
```

**Status Codes**:
- `200 OK`: Statistics retrieved

---

## WebSocket API

### Real-Time Scan Progress

Connect to receive real-time updates during a scan.

**Endpoint**: `WS /ws/scans/{scan_id}`

**Message Types**:

1. **Status Message** (initial connection):
```json
{
  "type": "status",
  "data": {
    "status": "running"
  }
}
```

2. **Progress Update** (periodic, every 500ms):
```json
{
  "type": "progress",
  "data": {
    "processed_count": 42,
    "total_files": 100,
    "progress_percentage": 42.0,
    "healthy_count": 38,
    "corrupt_count": 4,
    "suspicious_count": 0,
    "elapsed_time": 125.5
  }
}
```

3. **Completion Message**:
```json
{
  "type": "complete",
  "data": {
    "status": "completed",
    "error": null
  }
}
```

4. **Error Message**:
```json
{
  "type": "error",
  "data": {
    "message": "Error description"
  }
}
```

**Usage Example** (JavaScript):
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scans/550e8400-e29b-41d4-a716-446655440000');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch(message.type) {
    case 'progress':
      console.log(`Progress: ${message.data.progress_percentage}%`);
      break;
    case 'complete':
      console.log('Scan completed!');
      break;
    case 'error':
      console.error('Error:', message.data.message);
      break;
  }
};
```

---

## Security

The API implements several security measures:

### Path Traversal Protection

Directory paths are validated to prevent path traversal attacks:
- Paths are resolved to absolute paths
- Suspicious patterns (e.g., `..`, `~`) are rejected
- Non-existent or invalid paths return 400 Bad Request

### Information Disclosure Prevention

Error messages do not expose internal system details:
- Exception messages are logged but not returned to clients
- Generic error messages are returned (e.g., "Internal server error")
- Detailed errors are only available in server logs

### CORS Restrictions

Cross-Origin Resource Sharing is restricted to specific origins:
- Only localhost origins are allowed by default
- Production deployments should configure specific domains
- Methods and headers are explicitly whitelisted

### Input Validation

All request parameters are validated:
- Pydantic models enforce type checking
- Parameter ranges are enforced (e.g., max_workers: 1-32)
- Invalid inputs return 422 Unprocessable Entity

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Invalid input or path
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

---

## CORS Configuration

The API is configured with CORS to allow localhost origins for development:

**Allowed Origins (Default)**:
- `http://localhost:3000` - Docker frontend
- `http://localhost:5173` - Vite dev server
- `http://127.0.0.1:3000` - Docker frontend (IP)
- `http://127.0.0.1:5173` - Vite dev server (IP)

**Allowed Methods**:
- `GET`, `POST`, `DELETE`, `OPTIONS`

**Allowed Headers**:
- `Content-Type`, `Authorization`

For production deployments, add your domain to the `allowed_origins` list in `src/api/main.py`:

```python
allowed_origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

## Architecture

The API wraps existing core modules:

- **Scanner Integration**: Uses `src/core/scanner.VideoScanner` for video analysis
- **Configuration**: Loads settings from `src/config/config.py`
- **Models**: Leverages Pydantic models from `src/core/models/scanning`
- **No Duplication**: All business logic remains in core modules

---

## Future Enhancements

Planned features for future releases:

1. **File-Level Results**: Return individual file scan results
2. **Database Integration**: Query historical scans from SQLite database
3. **Authentication**: JWT-based authentication for multi-user deployments
4. **Query Builder**: Advanced filtering and search capabilities
5. **Export Endpoints**: Download results in CSV, JSON, PDF formats
6. **Trakt Integration**: Sync scan results with Trakt.tv watchlist
7. **Batch Operations**: Start multiple scans simultaneously
8. **Rate Limiting**: Prevent API abuse

---

## See Also

- [Web UI Documentation](WEB_UI.md)
- [Core Module Documentation](CORE.md)
- [Docker Deployment](DOCKER.md)
