# Corrupt Video Inspector Web UI

React-based web interface for video corruption detection with real-time progress monitoring.

## Overview

A modern web dashboard for managing video corruption scans. Features include:

- **New Scan Configuration**: Form-based interface for starting new scans
- **Real-time Progress**: WebSocket-based live updates during scanning
- **Scan History**: View all past and current scans with status
- **Results Visualization**: Clear display of corrupt vs healthy files

## Technology Stack

- **React 18** with TypeScript
- **Material-UI** for components and theming
- **Vite** for fast development and optimized builds
- **WebSocket** for real-time updates
- **Nginx** for production serving

## Development

### Prerequisites

- Node.js 18+
- API server running on port 8000

### Local Development

```bash
# Install dependencies
cd apps/web
npm install

# Set environment variables (optional)
cp .env.example .env
# Edit .env to set VITE_API_URL if API is not on localhost:8000

# Start development server (with proxy to API)
npm run dev

# Access at http://localhost:3000
```

### Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

## Docker Deployment

### Using Docker Compose

```bash
# From repository root
# Start both API and Web UI
docker compose --profile web up

# Or build and start
docker compose --profile web up --build

# Access:
# - Web UI: http://localhost:3000
# - API: http://localhost:8000
```

### Manual Docker Build

```bash
# Build image
docker build -f docker/Dockerfile.web -t cvi-web:latest apps/web/

# Run container
docker run -p 3000:3000 \
  -e VITE_API_URL=http://localhost:8000 \
  cvi-web:latest
```

## Features

### New Scan Tab

Configure and start new video corruption scans:
- Directory path selection
- Scan mode: Quick, Deep, or Hybrid
- Recursive subdirectory scanning
- Resume capability

### Scan Progress Tab

Monitor all scans with:
- List of all scans (past and present)
- Real-time status updates
- Auto-refresh every 5 seconds
- Click to view detailed results

### Results Tab

View detailed scan results with:
- Real-time progress bar during scanning
- Live file count updates
- Corrupt vs healthy file statistics
- Current file being scanned
- Final summary when complete

## API Integration

The web UI communicates with the FastAPI backend through:

**REST Endpoints:**
- `POST /api/scans` - Create new scan
- `GET /api/scans` - List all scans
- `GET /api/scans/{id}` - Get specific scan

**WebSocket:**
- `WS /ws/scans/{id}` - Real-time progress updates

## Configuration

Environment variables (set in `.env` file):

- `VITE_API_URL` - API server URL (default: `http://localhost:8000`)

## Architecture

```
apps/web/
├── src/
│   ├── api/
│   │   └── client.ts          # API client with REST and WebSocket
│   ├── components/
│   │   ├── ScanForm.tsx       # New scan configuration form
│   │   ├── ScanList.tsx       # List of all scans
│   │   └── ScanResults.tsx    # Detailed results with live updates
│   ├── App.tsx                # Main application with tab navigation
│   └── main.tsx               # Application entry point
├── index.html                  # HTML template
├── vite.config.ts             # Vite configuration with proxy
└── package.json               # Dependencies and scripts
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Troubleshooting

**Cannot connect to API:**
- Ensure API server is running on port 8000
- Check CORS settings in API configuration
- Verify `VITE_API_URL` in `.env` file

**WebSocket connection fails:**
- Check that API supports WebSocket connections
- Verify network allows WebSocket protocol
- Check browser console for detailed errors

**Build fails:**
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Ensure Node.js version is 18 or higher
