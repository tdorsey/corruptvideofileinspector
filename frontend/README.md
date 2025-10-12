# Corrupt Video Inspector - Web Frontend

React-based web interface for the Corrupt Video Inspector.

## Quick Start

### Prerequisites

- Node.js 18 or later
- npm 9 or later

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Start development server
npm run dev

# Development server will be available at http://localhost:5173
```

The development server includes:
- Hot module replacement
- API proxy to backend (http://localhost:8000)
- WebSocket proxy for real-time updates

### Building for Production

```bash
# Build production bundle
npm run build

# Preview production build locally
npm run preview
```

Production build outputs to `dist/` directory.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Lint TypeScript/React code
- `npm run format` - Format code with Prettier
- `npm run type-check` - Type check without emitting

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable React components
│   │   └── AppBar.tsx  # Navigation bar
│   ├── pages/          # Page components (routes)
│   │   ├── Dashboard.tsx   # System status dashboard
│   │   ├── ScanPage.tsx    # Scan configuration
│   │   └── ResultsPage.tsx # Scan results display
│   ├── services/       # API communication
│   │   └── api.ts      # API client methods
│   ├── types/          # TypeScript type definitions
│   │   └── api.ts      # API data models
│   ├── App.tsx         # Main app component
│   └── main.tsx        # Application entry point
├── public/             # Static assets
├── index.html          # HTML template
├── vite.config.ts      # Vite configuration
├── tsconfig.json       # TypeScript configuration
├── package.json        # Dependencies and scripts
└── README.md           # This file
```

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Material-UI (MUI)** - Component library
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **WebSocket API** - Real-time updates

## Configuration

### API Endpoint

The API endpoint is configured in `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

To use a different API server, modify the `target` URL.

### Environment Variables

Create a `.env.local` file for environment-specific configuration:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Development Guidelines

### Code Style

- Use functional components with hooks
- Follow TypeScript strict mode
- Use Material-UI components
- Format with Prettier (2 spaces, single quotes)
- Lint with ESLint

### Adding New Pages

1. Create component in `src/pages/`
2. Add route in `App.tsx`
3. Add navigation link in `AppBar.tsx`

Example:

```typescript
// src/pages/NewPage.tsx
import { Container, Typography } from '@mui/material'

export default function NewPage() {
  return (
    <Container>
      <Typography variant="h4">New Page</Typography>
    </Container>
  )
}

// App.tsx
<Route path="/new-page" element={<NewPage />} />
```

### API Integration

Use the `apiService` from `src/services/api.ts`:

```typescript
import { apiService } from '@/services/api'

// Health check
const health = await apiService.healthCheck()

// Start scan
const response = await apiService.startScan({
  directory: '/path/to/videos',
  mode: ScanMode.QUICK,
  recursive: true,
  max_workers: 8,
})

// WebSocket connection
const ws = apiService.createWebSocket(scanId)
ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  // Handle message
}
```

## Docker Deployment

The frontend is containerized for production deployment:

```bash
# Build Docker image
docker build -f ../docker/Dockerfile.frontend -t cvi-frontend ..

# Run with Docker Compose
docker-compose -f ../docker/docker-compose.web.yml up
```

The Docker build uses multi-stage builds:
1. Build stage: Compile TypeScript and bundle with Vite
2. Runtime stage: Serve static files with Nginx

## Troubleshooting

### "Module not found" errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Development server not proxying API

Check that the API server is running on port 8000:

```bash
curl http://localhost:8000/api/health
```

### Build fails with TypeScript errors

```bash
# Type check to see detailed errors
npm run type-check
```

### Hot reload not working

Clear Vite cache:

```bash
rm -rf node_modules/.vite
npm run dev
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Internet Explorer is not supported.

## Contributing

1. Follow the existing code style
2. Write TypeScript with strict types
3. Test changes in development mode
4. Ensure production build succeeds
5. Update documentation as needed

## Documentation

- [Web UI Guide](../docs/WEB_UI.md)
- [API Documentation](../docs/API.md)
- [Main Project README](../README.md)

## License

MIT
