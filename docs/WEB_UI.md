# Web UI Documentation

The Corrupt Video Inspector Web UI provides a modern, React-based graphical interface for managing video corruption scans.

## Overview

- **Frontend**: React 18 with TypeScript
- **UI Framework**: Material-UI (MUI) v5
- **Build Tool**: Vite
- **State Management**: React hooks and context
- **Real-Time Updates**: WebSocket connection to API

## Quick Start

### Prerequisites

- Node.js 18+ (for local development)
- Docker and Docker Compose (for container deployment)

### Local Development

```bash
# Install frontend dependencies
cd frontend
npm install

# Start the API server (in separate terminal)
cd ..
python api_server.py

# Start the frontend development server
cd frontend
npm run dev
```

The web UI will be available at `http://localhost:5173`.

### Docker Deployment

```bash
# Build and start all services
make web-docker-build
make web-docker-up
```

The web UI will be available at `http://localhost:3000`.

---

## Features

### Dashboard

The dashboard provides an overview of system status:

- **System Health**: Shows API server status
- **FFmpeg Status**: Indicates whether FFmpeg is available
- **API Version**: Displays current API version
- **Quick Actions**: Button to start a new scan

**Access**: Navigate to `/` or click "Dashboard" in the navigation bar.

---

### New Scan

The scan configuration page allows you to start a new video corruption scan:

**Fields**:
- **Directory Path**: Absolute path to the video directory (required)
- **Scan Mode**: 
  - **Quick**: Fast, basic checks (recommended for initial scans)
  - **Deep**: Thorough analysis (slower but more comprehensive)
  - **Hybrid**: Quick scan first, then deep scan on suspicious files (best of both worlds)
- **Max Workers**: Number of parallel scanning threads (1-32, default: 8)
- **Recursive**: Enable to scan subdirectories

**Features**:
- Real-time progress bar showing scan advancement
- Live statistics (healthy/corrupt/suspicious counts)
- Current file being processed
- Automatic navigation to results when scan completes

**Access**: Click "New Scan" in the navigation bar or the "Start New Scan" button on the dashboard.

---

### Scan Results

The results page displays comprehensive scan statistics and file details:

**Summary Cards**:
- Total Files: Number of files scanned
- Healthy Files: Files with no corruption detected
- Corrupt Files: Files identified as corrupt
- Suspicious Files: Files requiring further investigation

**Details Table**:
- Status indicator (icon and badge)
- File name
- File size (MB)
- Confidence percentage
- Issues detected
- Scan time per file

**Access**: Automatically redirected after scan completion, or navigate to `/results/{scan_id}`.

---

## Architecture

### Component Structure

```
frontend/src/
├── components/        # Reusable UI components
│   └── AppBar.tsx    # Navigation bar
├── pages/            # Page components
│   ├── Dashboard.tsx # Dashboard page
│   ├── ScanPage.tsx  # Scan configuration page
│   └── ResultsPage.tsx # Results display page
├── services/         # API client
│   └── api.ts        # API service methods
├── types/            # TypeScript type definitions
│   └── api.ts        # API data models
├── App.tsx           # Main application component
└── main.tsx          # Application entry point
```

### Technology Stack

**Core**:
- React 18.2+ - Component framework
- TypeScript 5.2+ - Type safety
- React Router 6.20+ - Client-side routing

**UI Components**:
- Material-UI (MUI) 5.14+ - Component library
- Emotion - CSS-in-JS styling
- MUI Icons - Icon set

**Data Fetching**:
- Axios 1.6+ - HTTP client
- WebSocket API - Real-time updates

**Development Tools**:
- Vite 5.0+ - Build tool and dev server
- ESLint 8.53+ - Code linting
- Prettier 3.1+ - Code formatting

---

## Development

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run type-check
```

### Code Style

The project enforces code style through ESLint and Prettier:

- **Semicolons**: Not used
- **Quotes**: Single quotes
- **Indent**: 2 spaces
- **Max line length**: 100 characters
- **Arrow functions**: Always use parentheses

### Adding New Pages

1. Create component in `frontend/src/pages/`:
```typescript
import { Container, Typography } from '@mui/material'

export default function NewPage() {
  return (
    <Container>
      <Typography variant="h4">New Page</Typography>
      {/* Page content */}
    </Container>
  )
}
```

2. Add route in `App.tsx`:
```typescript
<Route path="/new-page" element={<NewPage />} />
```

3. Add navigation link in `AppBar.tsx`:
```typescript
<Button color="inherit" onClick={() => navigate('/new-page')}>
  New Page
</Button>
```

---

## Docker Configuration

### Frontend Container

The frontend is built in a multi-stage Docker image:

1. **Build Stage**: Compiles TypeScript and bundles React app with Vite
2. **Runtime Stage**: Serves static files with Nginx

**Dockerfile**: `docker/Dockerfile.frontend`

### API Container

The API runs in a Python 3.13 container with FastAPI and Uvicorn.

**Dockerfile**: `docker/Dockerfile.api`

### Nginx Configuration

Nginx serves the React app and proxies API requests:

- **Static files**: Served from `/usr/share/nginx/html`
- **API proxy**: `/api/*` forwarded to `api:8000`
- **WebSocket proxy**: `/ws/*` forwarded to `api:8000`

**Configuration**: `docker/nginx.conf`

### Docker Compose

The `docker-compose.web.yml` orchestrates all services:

```yaml
services:
  api:      # FastAPI backend
  frontend: # React app with Nginx
networks:
  cvi-network: # Internal network
volumes:
  video_data:  # Video files (read-only)
  output:      # Scan results output
  logs:        # Application logs
```

**Environment Variables** (in `docker/.env`):
- `CVI_VIDEO_DIR`: Path to video directory
- `CVI_OUTPUT_DIR`: Path to output directory
- `CVI_LOG_DIR`: Path to log directory

---

## Configuration

### API Base URL

The frontend auto-detects the API URL. For custom configurations, update `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://custom-api-host:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### Build Options

Customize the build in `vite.config.ts`:

```typescript
export default defineConfig({
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'esbuild',
    target: 'es2020',
  },
})
```

---

## Troubleshooting

### Frontend Not Loading

**Symptom**: Blank page or "Cannot GET /" error

**Solutions**:
1. Check if Nginx is running: `docker ps`
2. Check browser console for errors
3. Verify nginx configuration: `docker logs cvi-frontend`

### API Connection Failed

**Symptom**: "Failed to connect to API server" error on dashboard

**Solutions**:
1. Verify API is running: `curl http://localhost:8000/api/health`
2. Check API logs: `docker logs cvi-api`
3. Ensure ports are not blocked by firewall

### WebSocket Connection Failed

**Symptom**: Progress updates not appearing during scan

**Solutions**:
1. Check WebSocket connection in browser dev tools (Network tab)
2. Verify nginx WebSocket proxy configuration
3. Check API WebSocket handler logs

### Build Failures

**Symptom**: `npm run build` fails

**Solutions**:
1. Clear node_modules: `rm -rf node_modules package-lock.json && npm install`
2. Check Node.js version: `node --version` (should be 18+)
3. Review TypeScript errors: `npm run type-check`

---

## Browser Support

The web UI supports modern browsers:

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Internet Explorer is not supported.

---

## Accessibility

The UI follows WCAG 2.1 Level AA guidelines:

- Keyboard navigation support
- Screen reader friendly
- High contrast mode compatible
- Semantic HTML elements
- ARIA labels where appropriate

---

## Performance

**Optimizations**:
- Code splitting by route
- Lazy loading of components
- Gzip compression in Nginx
- Efficient React rendering with memoization
- WebSocket connection pooling

**Metrics** (production build):
- Initial bundle size: ~300 KB (gzipped)
- First contentful paint: < 1.5s
- Time to interactive: < 3s

---

## Future Enhancements

Planned features for future releases:

1. **Historical Scans**: View and compare previous scan results
2. **Trend Charts**: Visualize corruption rates over time
3. **Database Query Builder**: Advanced filtering and search
4. **Batch Operations**: Select and export multiple results
5. **Dark Mode**: Toggle between light and dark themes
6. **Mobile Responsive**: Optimized layout for mobile devices
7. **Notifications**: Browser notifications for scan completion
8. **Export Reports**: Download results in CSV, JSON, or PDF formats

---

## See Also

- [API Documentation](API.md)
- [Docker Deployment](DOCKER.md)
- [Core Module Documentation](CORE.md)
