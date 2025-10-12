# Phase 1 MVP - Core Scanning UI Backend and Frontend

## Overview

Phase 1 MVP delivers a complete web-based interface for video corruption scanning with:
- FastAPI backend with REST endpoints
- Real-time progress monitoring via WebSocket
- React frontend with Material-UI
- Docker Compose deployment

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Web Browser   │◄──────►│   Nginx (3000)   │
│   (React App)   │   HTTP  │   + Web Assets   │
└─────────────────┘         └──────────────────┘
         │                           │
         │ WebSocket                 │ Proxy
         │ /ws/scans/{id}           │
         │                           ▼
         │                  ┌──────────────────┐
         └─────────────────►│  FastAPI (8000)  │
              REST API       │   + GraphQL      │
              /api/scans     └──────────────────┘
                                      │
                                      ▼
                             ┌──────────────────┐
                             │  Video Scanner   │
                             │  FFmpeg + Core   │
                             └──────────────────┘
```

## Backend API

### REST Endpoints

#### POST /api/scans
Create a new video scan.

**Request:**
```json
{
  "directory": "/path/to/videos",
  "scan_mode": "quick",
  "recursive": true,
  "resume": true
}
```

**Response:**
```json
{
  "id": "uuid",
  "directory": "/path/to/videos",
  "scan_mode": "quick",
  "status": "running",
  "started_at": "2025-10-12T20:00:00Z",
  "completed_at": null,
  "results_count": 0
}
```

#### GET /api/scans
List all scans.

**Response:**
```json
[
  {
    "id": "uuid",
    "directory": "/path/to/videos",
    "scan_mode": "quick",
    "status": "completed",
    "started_at": "2025-10-12T20:00:00Z",
    "completed_at": "2025-10-12T20:05:00Z",
    "results_count": 42
  }
]
```

#### GET /api/scans/{id}
Get specific scan details.

**Response:**
```json
{
  "id": "uuid",
  "directory": "/path/to/videos",
  "scan_mode": "hybrid",
  "status": "running",
  "started_at": "2025-10-12T20:00:00Z",
  "completed_at": null,
  "results_count": 0
}
```

### WebSocket Endpoint

#### WS /ws/scans/{id}
Real-time progress updates during scanning.

**Messages sent from server:**
```json
{
  "current_file": "/path/to/video.mp4",
  "processed_files": 25,
  "total_files": 100,
  "progress_percentage": 25.0,
  "corrupt_count": 3,
  "healthy_count": 22,
  "status": "running"
}
```

**Completion message:**
```json
{
  "current_file": "Complete",
  "processed_files": 100,
  "total_files": 100,
  "progress_percentage": 100.0,
  "corrupt_count": 5,
  "healthy_count": 95,
  "status": "completed"
}
```

**Error message:**
```json
{
  "status": "failed",
  "error": "Directory not found: /invalid/path",
  "progress_percentage": 0
}
```

## Frontend UI

### Components

#### ScanForm
- Directory path input field
- Scan mode selector (Quick/Deep/Hybrid)
- Recursive scanning toggle
- Resume capability toggle
- Submit button with loading state
- Error display

#### ScanList
- Displays all scans with status chips
- Auto-refreshes every 5 seconds
- Click to view details
- Color-coded status indicators:
  - Green: Completed
  - Blue: Running
  - Red: Failed

#### ScanResults
- Real-time progress bar during scanning
- Live file count updates via WebSocket
- Statistics cards:
  - Healthy files count
  - Corrupt files count
- Current file being processed
- Scan metadata (directory, mode, timestamps)

### Navigation

Three-tab interface:
1. **New Scan** - Configure and start scans
2. **Scan Progress** - View all scans and their status
3. **Results** - Detailed view with live updates

## Deployment

### Docker Compose (Recommended)

```bash
# Start both API and Web UI
docker compose --profile web up

# Or build first
docker compose --profile web build
docker compose --profile web up

# Access:
# - Web UI: http://localhost:3000
# - API: http://localhost:8000
# - GraphQL: http://localhost:8000/graphql
```

### Development Setup

**Backend:**
```bash
# Install dependencies
make install-dev

# Start API server
make run-api
# or
python -m uvicorn src.api.app:create_app --factory --reload
```

**Frontend:**
```bash
cd apps/web

# Install dependencies
npm install

# Start dev server (with API proxy)
npm run dev
```

## Features

### Implemented ✅

- [x] REST API for scan operations
- [x] WebSocket real-time progress updates
- [x] Connection management for multiple clients
- [x] React frontend with TypeScript
- [x] Material-UI component library
- [x] Form-based scan configuration
- [x] Real-time progress monitoring
- [x] Scan list with auto-refresh
- [x] Results visualization
- [x] Docker containerization
- [x] Nginx reverse proxy for production
- [x] CORS configuration
- [x] Error handling and display

### Future Enhancements 🚀

- [ ] Scan result details (individual file results)
- [ ] Download results as JSON/CSV
- [ ] Cancel running scans
- [ ] Scan history persistence (database)
- [ ] User authentication
- [ ] Multiple concurrent scans
- [ ] Scan scheduling
- [ ] Email notifications on completion
- [ ] Advanced filtering and search
- [ ] Scan comparison
- [ ] Performance metrics dashboard

## Configuration

### Backend (.env or config.yaml)
```yaml
api:
  enabled: true
  host: "0.0.0.0"
  port: 8000
  oidc_enabled: false
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

### Docker Compose
```yaml
services:
  api:
    ports:
      - "8000:8000"
    profiles:
      - web
      
  web:
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - api
    profiles:
      - web
```

## Testing

### API Tests
```bash
# Run API unit tests
pytest tests/unit/test_api.py -v

# Test API manually
curl http://localhost:8000/health

# Create a scan
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"directory": "/app/videos", "scan_mode": "quick"}'
```

### Frontend Tests
```bash
cd apps/web

# Type checking
npx tsc --noEmit

# Build test
npm run build
```

### Integration Test
1. Start API: `make run-api`
2. Start Web: `cd apps/web && npm run dev`
3. Open browser: http://localhost:3000
4. Configure and start a scan
5. Monitor real-time progress
6. View results

## Troubleshooting

### API won't start
- Check port 8000 is available: `lsof -i :8000`
- Verify config.yaml exists
- Check Python dependencies installed: `make install-dev`

### WebSocket connection fails
- Ensure API is running
- Check CORS configuration
- Verify firewall allows WebSocket protocol
- Check browser console for errors

### Frontend build fails
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)
- Verify all dependencies installed

### Docker build fails
- Check Docker daemon is running
- Verify Dockerfile.web exists
- Check available disk space
- Try without cache: `docker compose build --no-cache`

## Security Considerations

### Current Implementation
- CORS enabled for all origins (development)
- No authentication required
- In-memory storage (data lost on restart)

### Production Recommendations
- Configure CORS for specific origins
- Enable OIDC authentication
- Use database for persistence
- Add rate limiting
- Enable HTTPS/WSS
- Implement input validation
- Add request logging
- Use secrets management

## Performance

### Current Limitations
- Single scan at a time
- In-memory storage only
- No scan queue
- WebSocket per scan

### Optimization Opportunities
- Add scan queue with priority
- Implement database storage
- Cache scan results
- Optimize WebSocket broadcasting
- Add pagination for scan list
- Implement lazy loading

## References

- [API Documentation](./API.md)
- [Web App README](../apps/web/README.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Material-UI Documentation](https://mui.com/)
- [WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
