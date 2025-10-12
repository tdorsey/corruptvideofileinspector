# API Usage Examples

This directory contains example scripts demonstrating how to use the Corrupt Video Inspector GraphQL API.

## Prerequisites

1. **Start the API server**:

   ```bash
   # Option 1: Run locally
   make run-api

   # Option 2: Run with Docker
   make docker-api
   ```

2. **Install required Python packages** (for the example scripts):

   ```bash
   pip install requests
   ```

## Examples

### api_example.py

A comprehensive example demonstrating the full API workflow:

- Health checks and API metadata
- Starting video scans via GraphQL mutations
- Querying scan jobs and results
- Retrieving scan summaries
- Generating reports

**Usage**:

```bash
python examples/api_example.py
```

**Expected Output**:

```
============================================================
Corrupt Video Inspector - GraphQL API Example
============================================================
✓ API is healthy: {'status': 'healthy', 'service': 'corrupt-video-inspector-api'}

API Information:
  Name: Corrupt Video Inspector API
  Version: 1.0.0
  GraphQL Endpoint: /graphql

------------------------------------------------------------
Starting a new scan...
------------------------------------------------------------
✓ Scan started successfully!
  Job ID: 123e4567-e89b-12d3-a456-426614174000
  Directory: /app/videos
  Mode: QUICK
  Status: running

...
```

## GraphQL Query Examples

### 1. Start a Scan

```graphql
mutation {
  startScan(input: {
    directory: "/path/to/videos"
    scanMode: HYBRID
    recursive: true
  }) {
    id
    status
    directory
  }
}
```

### 2. Get All Scan Jobs

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

### 3. Get Scan Summary

```graphql
query {
  scanSummary(jobId: "your-job-id") {
    totalFiles
    corruptFiles
    healthyFiles
    successRate
  }
}
```

### 4. Generate Report

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

## Using cURL

### Health Check

```bash
curl http://localhost:8000/health
```

### GraphQL Query

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ scanJobs { id directory status } }"
  }'
```

### GraphQL Mutation with Variables

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation($dir: String!) { startScan(input: { directory: $dir, scanMode: QUICK }) { id status } }",
    "variables": { "dir": "/app/videos" }
  }'
```

## Authentication (OIDC)

When OIDC authentication is enabled, include the JWT token in the Authorization header:

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "query": "{ scanJobs { id } }"
  }'
```

## GraphQL Playground

The API includes a GraphQL playground for interactive exploration:

1. Open your browser to: http://localhost:8000/graphql
2. Use the built-in documentation explorer
3. Try queries and mutations interactively

## Troubleshooting

### API Not Accessible

**Error**: Connection refused on port 8000

**Solution**:
- Ensure the API is running: `make run-api` or `make docker-api`
- Check if port 8000 is already in use: `lsof -i :8000`
- Verify the API container is healthy: `docker ps` and `docker logs cvi-api`

### GraphQL Errors

**Error**: GraphQL returns error responses

**Solution**:
- Check the error message in the response
- Verify the query syntax matches the schema
- Ensure required fields are provided
- Check API logs for detailed error information

### Authentication Errors

**Error**: 401 Unauthorized

**Solution**:
- Verify OIDC is configured correctly if enabled
- Check that the JWT token is valid and not expired
- Ensure the token is included in the Authorization header
- For development, set `OIDC_ENABLED=false` in config

## Next Steps

- Review the [API Documentation](../docs/API.md) for the complete schema
- Check the [Configuration Guide](../docs/CONFIG.md) for API settings
- See [Docker Documentation](../docs/DOCKER.md) for deployment options
