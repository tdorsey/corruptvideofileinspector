# API Module Documentation

The API module (`src/api/`) provides a FastAPI-based GraphQL API for the Corrupt Video Inspector. It enables web-based interaction with the video scanning and reporting functionality through a modern, type-safe GraphQL interface.

## Architecture

```
src/api/
├── __init__.py              # Module exports
├── __main__.py              # Entry point for running the API server
├── app.py                   # FastAPI application setup
├── security.py              # OIDC authentication and authorization
└── graphql/                 # GraphQL schema and resolvers
    ├── __init__.py
    ├── schema.py            # GraphQL schema definition
    ├── types.py             # GraphQL type definitions (Strawberry)
    └── resolvers.py         # Query and mutation resolvers
```

## Features

- **GraphQL API**: Type-safe API using Strawberry GraphQL
- **Database History & Analytics**: Query scan history, statistics, and corruption trends
- **OIDC Authentication**: Secure API access with OpenID Connect
- **RESTful Endpoints**: Health check and metadata endpoints
- **Docker Support**: Containerized deployment with docker-compose
- **Async Operations**: Non-blocking video scanning and reporting
- **CORS Support**: Configurable cross-origin resource sharing

## Quick Start

### Running Locally

1. **Install dependencies**:
   ```bash
   make install-dev
   ```

2. **Configure the API** in `config.yaml`:
   ```yaml
   api:
     enabled: true
     host: "0.0.0.0"
     port: 8000
     oidc_enabled: false
   ```

3. **Run the API server**:
   ```bash
   # Using Make
   make run-api

   # Using Nx (if node_modules installed)
   npx nx serve api
   ```

   Or directly with uvicorn:
   ```bash
   python -m uvicorn src.api.app:create_app --factory --reload
   ```

4. **Access the API**:
   - GraphQL Playground: http://localhost:8000/graphql
   - Health Check: http://localhost:8000/health
   - API Info: http://localhost:8000/

### Running with Docker

1. **Build the API image**:
   ```bash
   make docker-api-build
   # Or with Nx
   npx nx build api
   ```

2. **Run the API container**:
   ```bash
   make docker-api
   # Or with Nx
   npx nx docker-up api
   ```

3. **Stop the API container**:
   ```bash
   make docker-api-down
   # Or with Nx
   npx nx docker-down api
   ```

### Running with Nx

The API project is integrated with Nx for workspace orchestration:

```bash
# Install Nx dependencies (first time only)
npm install

# Run API server with hot reload
npx nx serve api

# Build Docker image
npx nx build api

# Run tests
npx nx test api

# Lint code
npx nx lint api

# Format code
npx nx format api

# Start Docker container
npx nx docker-up api

# Stop Docker container
npx nx docker-down api
```

**Benefits of using Nx:**
- **Caching**: Task results are cached for faster rebuilds
- **Affected commands**: Only test/build changed code
- **Dependency graph**: Visualize project dependencies
- **Parallel execution**: Run tasks in parallel

See [`NX_QUICK_START.md`](../NX_QUICK_START.md) for more Nx commands.

## GraphQL Schema

### Types

#### ScanModeType
```graphql
enum ScanModeType {
  QUICK
  DEEP
  HYBRID
}
```

#### FileStatusType
```graphql
enum FileStatusType {
  HEALTHY
  CORRUPT
  NEEDS_DEEP_SCAN
  ERROR
}
```

#### ScanResultType
```graphql
type ScanResultType {
  path: String!
  isCorrupt: Boolean!
  confidence: Float!
  errorMessage: String
  fileSizeBytes: Int!
  scanMode: ScanModeType!
  status: FileStatusType!
  needsDeepScan: Boolean!
  scannedAt: DateTime!
}
```

#### ScanSummaryType
```graphql
type ScanSummaryType {
  directory: String!
  totalFiles: Int!
  processedFiles: Int!
  corruptFiles: Int!
  healthyFiles: Int!
  scanMode: ScanModeType!
  scanTimeSeconds: Float!
  successRate: Float!
  filesPerSecond: Float!
  startedAt: DateTime!
  completedAt: DateTime
}
```

#### ScanJobType
```graphql
type ScanJobType {
  id: String!
  directory: String!
  scanMode: ScanModeType!
  status: String!
  startedAt: DateTime!
  completedAt: DateTime
  resultsCount: Int!
}
```

#### ReportType
```graphql
type ReportType {
  id: String!
  format: String!
  filePath: String!
  createdAt: DateTime!
  scanSummary: ScanSummaryType!
}
```

#### DatabaseStatsType
```graphql
type DatabaseStatsType {
  totalScans: Int!
  totalFiles: Int!
  corruptFiles: Int!
  healthyFiles: Int!
  oldestScan: Float
  newestScan: Float
  databaseSizeBytes: Int!
}
```

#### CorruptionTrendDataType
```graphql
type CorruptionTrendDataType {
  scanDate: String!
  corruptFiles: Int!
  totalFiles: Int!
  corruptionRate: Float!
}
```

#### ScanHistoryType
```graphql
type ScanHistoryType {
  id: Int!
  directory: String!
  scanMode: String!
  startedAt: Float!
  completedAt: Float
  totalFiles: Int!
  processedFiles: Int!
  corruptFiles: Int!
  healthyFiles: Int!
  successRate: Float!
  scanTime: Float!
}
```

#### ScanResultHistoryType
```graphql
type ScanResultHistoryType {
  id: Int!
  scanId: Int!
  filename: String!
  fileSize: Int!
  isCorrupt: Boolean!
  confidence: Float!
  inspectionTime: Float!
  scanMode: String!
  status: String!
  createdAt: Float!
}
```

#### DatabaseQueryFilterInput
```graphql
input DatabaseQueryFilterInput {
  directory: String
  isCorrupt: Boolean
  scanMode: String
  minConfidence: Float
  maxConfidence: Float
  minFileSize: Int
  maxFileSize: Int
  sinceDate: Float
  untilDate: Float
  filenamePattern: String
  limit: Int
  offset: Int = 0
}
```

### Queries

#### Get All Scan Jobs
```graphql
query {
  scanJobs {
    id
    directory
    scanMode
    status
    startedAt
    completedAt
    resultsCount
  }
}
```

#### Get Specific Scan Job
```graphql
query {
  scanJob(jobId: "uuid-here") {
    id
    directory
    status
    resultsCount
  }
}
```

#### Get Scan Results
```graphql
query {
  scanResults(jobId: "uuid-here") {
    path
    isCorrupt
    confidence
    status
    fileSizeBytes
  }
}
```

#### Get Scan Summary
```graphql
query {
  scanSummary(jobId: "uuid-here") {
    directory
    totalFiles
    corruptFiles
    healthyFiles
    scanTimeSeconds
    successRate
  }
}
```

#### Get Database Statistics
```graphql
query {
  databaseStats {
    totalScans
    totalFiles
    corruptFiles
    healthyFiles
    oldestScan
    newestScan
    databaseSizeBytes
  }
}
```

#### Query Database Results
```graphql
query {
  databaseQuery(filter: {
    directory: "/path/to/videos"
    isCorrupt: true
    minConfidence: 0.8
    limit: 50
    offset: 0
  }) {
    id
    scanId
    filename
    fileSize
    isCorrupt
    confidence
    inspectionTime
    scanMode
    status
    createdAt
  }
}
```

#### Get Corruption Trend
```graphql
query {
  corruptionTrend(directory: "/path/to/videos", days: 30) {
    scanDate
    corruptFiles
    totalFiles
    corruptionRate
  }
}
```

#### Get Scan History
```graphql
query {
  scanHistory(limit: 10) {
    id
    directory
    scanMode
    startedAt
    completedAt
    totalFiles
    processedFiles
    corruptFiles
    healthyFiles
    successRate
    scanTime
  }
}
```

### Mutations

#### Start a Scan
```graphql
mutation {
  startScan(input: {
    directory: "/path/to/videos"
    scanMode: HYBRID
    recursive: true
    resume: true
  }) {
    id
    directory
    status
    startedAt
  }
}
```

#### Generate Report
```graphql
mutation {
  generateReport(input: {
    scanJobId: "uuid-here"
    format: "json"
    includeHealthy: false
    prettyPrint: true
  }) {
    id
    format
    filePath
    createdAt
    scanSummary {
      totalFiles
      corruptFiles
    }
  }
}
```

## Authentication

### OIDC Configuration

The API supports OpenID Connect (OIDC) authentication for secure access.

#### Environment Variables

```bash
export OIDC_ENABLED=true
export OIDC_ISSUER=https://auth.example.com
export OIDC_CLIENT_ID=your-client-id
export OIDC_CLIENT_SECRET=your-client-secret
export OIDC_AUDIENCE=corrupt-video-inspector-api
```

#### Configuration File

```yaml
api:
  enabled: true
  oidc_enabled: true
  oidc_issuer: "https://auth.example.com"
  oidc_client_id: "your-client-id"
  oidc_client_secret: "your-client-secret"
  oidc_audience: "corrupt-video-inspector-api"
```

#### Using Bearer Tokens

When OIDC is enabled, include the JWT token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/graphql \
     -d '{"query": "{ scanJobs { id } }"}'
```

### Development Mode (No Authentication)

For development purposes, OIDC can be disabled:

```yaml
api:
  enabled: true
  oidc_enabled: false
```

## REST Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "corrupt-video-inspector-api"
}
```

### API Metadata

```bash
GET /
```

Response:
```json
{
  "name": "Corrupt Video Inspector API",
  "version": "1.0.0",
  "graphql_endpoint": "/graphql",
  "health_endpoint": "/health"
}
```

## Docker Deployment

### Docker Compose Configuration

The API service is defined in `docker/docker-compose.yml`:

```yaml
services:
  api:
    image: cvi-api:1.0.0
    build:
      context: ..
      dockerfile: docker/Dockerfile.api
    container_name: cvi-api
    ports:
      - "8000:8000"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - video_data:/app/videos:ro
      - output:/app/output:ro
    environment:
      - OIDC_ENABLED=false
      - PYTHONUNBUFFERED=1
    profiles:
      - api
```

### Running with Profiles

The API service uses Docker Compose profiles to avoid running by default:

```bash
# Run only the API
docker compose --profile api up

# Run API alongside other services
docker compose --profile api --profile trakt up
```

## Integration with Core Components

The API integrates with the core functionality through:

- **ScanHandler**: Executes video scans using the CLI handler
- **ReportService**: Generates reports in various formats
- **VideoScanner**: Orchestrates file scanning operations
- **Configuration**: Uses the centralized AppConfig system

## Development

### Adding New Queries

1. Define the query in `src/api/graphql/resolvers.py`:
   ```python
   @strawberry.field
   def my_new_query(self, info: Info, param: str) -> MyType:
       # Implementation
       pass
   ```

2. Add the query to the `Query` class

3. Update the GraphQL schema automatically (Strawberry handles this)

### Adding New Mutations

1. Define the mutation in `src/api/graphql/resolvers.py`:
   ```python
   @strawberry.mutation
   def my_new_mutation(self, info: Info, input: MyInputType) -> MyOutputType:
       # Implementation
       pass
   ```

2. Add the mutation to the `Mutation` class

### Adding New Types

1. Define types in `src/api/graphql/types.py`:
   ```python
   @strawberry.type
   class MyNewType:
       field1: str
       field2: int
   ```

2. Use the types in queries and mutations

## Testing

### Unit Tests

```bash
pytest tests/unit/test_api.py -v
```

### Integration Tests

```bash
# Start the API
make run-api

# In another terminal, run integration tests
pytest tests/integration/test_api_integration.py -v
```

### Manual Testing with cURL

```bash
# Health check
curl http://localhost:8000/health

# GraphQL query
curl -X POST http://localhost:8000/graphql \
     -H "Content-Type: application/json" \
     -d '{"query": "{ scanJobs { id directory status } }"}'

# Start a scan
curl -X POST http://localhost:8000/graphql \
     -H "Content-Type: application/json" \
     -d '{"query": "mutation { startScan(input: { directory: \"/app/videos\", scanMode: QUICK }) { id status } }"}'
```

## Security Considerations

1. **OIDC Authentication**: Always enable OIDC in production
2. **CORS Configuration**: Restrict allowed origins in production
3. **Rate Limiting**: Consider adding rate limiting for production use
4. **Input Validation**: All inputs are validated by Pydantic models
5. **File Access**: API only has read access to video files

## Performance

- **Async Operations**: GraphQL resolvers run asynchronously
- **Non-Blocking**: Video scans don't block API requests
- **Resource Limits**: Consider container resource limits for large scans
- **Caching**: Future enhancement for caching scan results

## Troubleshooting

### API Won't Start

1. Check configuration file exists: `config.yaml`
2. Verify dependencies are installed: `make install-dev`
3. Check port 8000 is not in use: `lsof -i :8000`

### GraphQL Queries Fail

1. Check GraphQL syntax in playground
2. Verify authentication token if OIDC is enabled
3. Check API logs for detailed error messages

### Docker Container Issues

1. Check container logs: `docker logs cvi-api`
2. Verify volumes are mounted: `docker inspect cvi-api`
3. Check network connectivity: `docker network inspect`

## Future Enhancements

- [ ] WebSocket subscriptions for real-time scan progress
- [x] Database integration for persistent scan history
- [ ] Batch operations for multiple scans
- [x] Advanced filtering and sorting for database queries
- [ ] Trakt.tv integration through GraphQL
- [ ] File upload support for scanning
- [ ] Admin panel integration
- [ ] Metrics and monitoring endpoints
- [ ] Interactive visualization charts for corruption trends

## Related Documentation

- [Core Module](./CORE.md) - Business logic components
- [CLI Module](./CLI.md) - Command-line interface
- [Configuration](./CONFIG.md) - Configuration management
- [Docker](./DOCKER.md) - Container deployment
