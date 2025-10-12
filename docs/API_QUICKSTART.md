# FastAPI GraphQL API - Quick Start Guide

This guide will help you get started with the Corrupt Video Inspector GraphQL API in just a few minutes.

## What is the API?

The FastAPI GraphQL API provides a web-based interface to the corrupt video file inspector, enabling:

- **Web UI Integration**: Build web frontends using React, Vue, or any modern framework
- **Programmatic Access**: Integrate video scanning into your workflows via API calls
- **Real-time Queries**: Query scan results and job status through GraphQL
- **Secure Access**: Optional OIDC authentication for production deployments

## 5-Minute Setup

### Prerequisites

- Docker and Docker Compose installed
- Configuration file (`config.yaml`) at the project root

### Step 1: Configure the API

Add this section to your `config.yaml`:

```yaml
api:
  enabled: true
  host: "0.0.0.0"
  port: 8000
  oidc_enabled: false  # Set to true for production
```

### Step 2: Start the API

```bash
# Using Docker Compose (recommended)
docker compose -f docker/docker-compose.yml --profile api up -d

# Or build and run manually
make docker-api-build
make docker-api
```

### Step 3: Verify It's Running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"corrupt-video-inspector-api"}
```

### Step 4: Access the GraphQL Playground

Open your browser to: **http://localhost:8000/graphql**

You'll see the GraphiQL interface where you can explore the schema and run queries.

## Your First Query

Try this query in the GraphQL playground:

```graphql
query {
  scanJobs {
    id
    directory
    status
    resultsCount
  }
}
```

## Your First Mutation

Start a video scan:

```graphql
mutation {
  startScan(input: {
    directory: "/app/videos"
    scanMode: QUICK
    recursive: true
  }) {
    id
    status
    directory
    startedAt
  }
}
```

## Common Use Cases

### 1. Check Scan Status

```graphql
query {
  scanJob(jobId: "your-job-id") {
    id
    status
    resultsCount
    startedAt
    completedAt
  }
}
```

### 2. Get Scan Results

```graphql
query {
  scanSummary(jobId: "your-job-id") {
    totalFiles
    corruptFiles
    healthyFiles
    successRate
    scanTimeSeconds
  }
}
```

### 3. Generate Report

```graphql
mutation {
  generateReport(input: {
    scanJobId: "your-job-id"
    format: "json"
    includeHealthy: false
  }) {
    id
    filePath
    format
  }
}
```

## Using from Python

```python
import requests

# Query scan jobs
response = requests.post(
    "http://localhost:8000/graphql",
    json={
        "query": """
            query {
                scanJobs {
                    id
                    directory
                    status
                }
            }
        """
    }
)

jobs = response.json()["data"]["scanJobs"]
print(f"Found {len(jobs)} scan jobs")
```

See `examples/api_example.py` for a complete working example.

## Using from JavaScript

```javascript
// Using fetch API
const query = `
  query {
    scanJobs {
      id
      directory
      status
    }
  }
`;

fetch('http://localhost:8000/graphql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query })
})
  .then(res => res.json())
  .then(data => console.log(data.data.scanJobs));
```

## Using from cURL

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ scanJobs { id directory status } }"}'
```

## Production Setup

For production deployments, enable OIDC authentication:

### 1. Update Configuration

```yaml
api:
  enabled: true
  oidc_enabled: true
  oidc_issuer: "https://auth.yourcompany.com"
  oidc_client_id: "your-client-id"
  oidc_client_secret: "your-client-secret"
  oidc_audience: "corrupt-video-inspector-api"
```

### 2. Set Environment Variables

```bash
export OIDC_ENABLED=true
export OIDC_ISSUER=https://auth.yourcompany.com
export OIDC_CLIENT_ID=your-client-id
export OIDC_CLIENT_SECRET=your-client-secret
export OIDC_AUDIENCE=corrupt-video-inspector-api
```

### 3. Include JWT Token in Requests

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"query": "{ scanJobs { id } }"}'
```

## Available Scan Modes

- **QUICK**: Fast scan using basic FFmpeg checks (~5-10 seconds per file)
- **DEEP**: Thorough scan analyzing entire file (~30-60 seconds per file)
- **HYBRID**: Quick scan first, then deep scan if issues detected

## Available Report Formats

- **json**: Machine-readable JSON format
- **csv**: Spreadsheet-compatible CSV format
- **yaml**: Human-readable YAML format
- **text**: Plain text report

## Troubleshooting

### API Won't Start

**Problem**: Container fails to start or exits immediately

**Solution**:
1. Check logs: `docker logs cvi-api`
2. Verify config file exists at project root
3. Ensure port 8000 is available: `lsof -i :8000`

### GraphQL Errors

**Problem**: Queries return error responses

**Solution**:
1. Check query syntax in GraphQL playground
2. Verify field names match the schema (use autocomplete)
3. Check API logs for detailed error messages

### Connection Refused

**Problem**: Cannot connect to http://localhost:8000

**Solution**:
1. Verify API is running: `docker ps | grep cvi-api`
2. Check container health: `docker inspect cvi-api`
3. Ensure you're using the correct port (8000 by default)

## Next Steps

- **Full Documentation**: See [API.md](./API.md) for complete schema reference
- **Examples**: Check `examples/api_example.py` for working code
- **Configuration**: Review [CONFIG.md](./CONFIG.md) for all API settings
- **Security**: Read about OIDC setup for production deployments
- **Docker**: See [DOCKER.md](./DOCKER.md) for advanced container configuration

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check docs/ directory for detailed guides
- **Examples**: See examples/ directory for working code samples

## Architecture Overview

```
┌─────────────────┐
│   Web Browser   │
│   or Client     │
└────────┬────────┘
         │ HTTP/GraphQL
         ▼
┌─────────────────┐
│   FastAPI       │
│   GraphQL API   │◄──── OIDC Auth (optional)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Core Services  │
│  - Scanner      │
│  - Reporter     │
│  - FFmpeg       │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Video Files   │
└─────────────────┘
```

## Key Features

✅ **Type-Safe**: GraphQL schema ensures type safety across your stack
✅ **Self-Documenting**: Built-in GraphQL playground with schema explorer
✅ **Async**: Non-blocking operations for better performance
✅ **Secure**: Optional OIDC authentication for production use
✅ **Containerized**: Easy deployment with Docker
✅ **Language Agnostic**: Use from any language that supports HTTP/GraphQL

## Roadmap

Future enhancements planned:

- [ ] WebSocket subscriptions for real-time progress updates
- [ ] Batch scan operations
- [ ] Advanced filtering and pagination
- [ ] Trakt.tv integration via GraphQL
- [ ] File upload support
- [ ] Admin dashboard integration
- [ ] Prometheus metrics endpoint

---

**Ready to build your web UI?** Start with the GraphQL playground and explore the schema!
