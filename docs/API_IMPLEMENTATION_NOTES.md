# API Implementation Notes

This document contains technical notes about the FastAPI GraphQL API implementation.

## Implementation Status

✅ **Complete** - All core functionality implemented and documented

## Architecture Decisions

### FastAPI + Strawberry GraphQL

We chose FastAPI with Strawberry GraphQL for several reasons:

1. **Type Safety**: Strawberry uses Python type hints for schema generation, ensuring type safety across the stack
2. **Modern Python**: Leverages Python 3.13 features and async/await patterns
3. **Auto-Documentation**: GraphQL playground provides built-in schema exploration
4. **Performance**: FastAPI is one of the fastest Python frameworks
5. **Ecosystem**: Rich ecosystem with OIDC, validation, and testing support

### OIDC Authentication

The API includes OIDC authentication support with the following design:

- **Configurable**: Can be enabled/disabled via configuration
- **Placeholder Implementation**: JWT verification is stubbed for extensibility
- **Production Ready**: Framework is in place for proper JWT validation

**To implement full JWT verification:**

```python
from authlib.jose import jwt
from authlib.jose.errors import JWTError

# In security.py verify_token function
def verify_jwt(token: str, oidc_config: OIDCConfig):
    # Fetch JWKS from OIDC provider
    jwks_url = f"{oidc_config.issuer}/.well-known/jwks.json"
    keys = requests.get(jwks_url).json()
    
    # Verify and decode token
    claims = jwt.decode(token, keys)
    claims.validate()
    
    return claims
```

### In-Memory Storage

Current implementation uses in-memory dictionaries for:

- Scan job tracking (`_scan_jobs`)
- Scan results storage (`_scan_results`)

**For production**, integrate with the database module:

```python
from src.database import DatabaseService

# In resolvers.py
db = DatabaseService(config)
scan_jobs = db.get_all_scans()
```

### GraphQL Schema Design

The schema follows these principles:

1. **Flat Structure**: Avoid deep nesting for better query performance
2. **Nullable Fields**: Use Optional types for fields that may not always be present
3. **Enums**: Type-safe enumerations for modes and statuses
4. **Input Types**: Separate input types for mutations to allow validation

### Integration with Core Services

The API integrates with existing services through:

1. **ScanHandler**: Reuses CLI scan logic for consistency
2. **ReportService**: Leverages existing report generation
3. **AppConfig**: Uses centralized configuration system

This approach ensures:
- Code reuse and consistency
- Single source of truth for business logic
- Easy maintenance and testing

## File Organization

```
src/api/
├── __init__.py           # Module exports
├── __main__.py           # CLI entry point (python -m src.api)
├── app.py               # FastAPI application setup
├── security.py          # OIDC authentication
└── graphql/
    ├── __init__.py
    ├── schema.py        # GraphQL schema definition
    ├── types.py         # Type definitions (Strawberry)
    └── resolvers.py     # Query and mutation logic
```

**Design Rationale:**
- Clear separation of concerns
- GraphQL logic isolated in subdirectory
- Security concerns separate from business logic
- Easy to locate and modify specific functionality

## Dependencies Added

```toml
dependencies = [
    # ... existing dependencies ...
    "fastapi>=0.115.0",              # Web framework
    "strawberry-graphql[fastapi]>=0.247.0",  # GraphQL
    "uvicorn[standard]>=0.32.0",     # ASGI server
    "python-multipart>=0.0.20",      # Form data support
    "authlib>=1.3.0",                # OIDC/OAuth
]
```

**Version Constraints:**
- Minimum versions specified for security and features
- Compatible with Python 3.13
- No upper bounds to allow flexibility

## Configuration Schema

Added `APIConfig` to `src/config/config.py`:

```python
class APIConfig(BaseModel):
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    oidc_enabled: bool = False
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_audience: str = ""
```

**Design Considerations:**
- Disabled by default to avoid breaking existing deployments
- All OIDC fields optional to support gradual adoption
- Host and port configurable for different deployment scenarios

## Docker Integration

### Dockerfile.api

Multi-stage build with:

1. **Base Stage**: System dependencies (FFmpeg, build tools)
2. **Dependencies Stage**: Python packages via Poetry
3. **Production Stage**: Minimal runtime image

**Security Features:**
- Non-root user (inspector:1000)
- Read-only config mount
- Minimal attack surface

### Docker Compose Profile

API uses the `api` profile to:
- Avoid running by default
- Allow selective service startup
- Maintain backward compatibility

**Usage:**
```bash
# Run only API
docker compose --profile api up

# Run API with other services
docker compose --profile api --profile trakt up
```

## Testing Strategy

### Unit Tests

Located in `tests/unit/test_api.py` and `test_api_config.py`:

- FastAPI TestClient for endpoint testing
- Mock configuration to avoid dependencies
- pytest markers for organization

### Integration Testing

For full integration tests (future work):

1. Start API container
2. Run example scripts
3. Verify GraphQL responses
4. Check database persistence
5. Test OIDC flow

### Manual Testing

Use the provided example script:
```bash
python examples/api_example.py
```

## Performance Considerations

### Async Operations

All resolvers use async/await:
- Non-blocking I/O operations
- Better resource utilization
- Improved throughput under load

### Potential Optimizations

1. **Caching**: Cache scan results for repeated queries
2. **Pagination**: Add pagination for large result sets
3. **DataLoader**: Use for N+1 query prevention
4. **Connection Pooling**: For database connections

## Security Considerations

### Current Implementation

✅ CORS configuration
✅ OIDC authentication framework
✅ Input validation via Pydantic
✅ Type safety via Strawberry

### Production Requirements

⚠️ **TODO** before production:

1. **JWT Verification**: Implement proper token validation
2. **Rate Limiting**: Add rate limiting middleware
3. **CORS Origins**: Restrict to specific domains
4. **API Keys**: Consider API key authentication as alternative
5. **Audit Logging**: Log all API access
6. **Input Sanitization**: Validate file paths and parameters

## Error Handling

### GraphQL Error Responses

Errors are returned in GraphQL format:

```json
{
  "errors": [
    {
      "message": "Scan failed: directory not found",
      "path": ["startScan"],
      "extensions": {
        "code": "SCAN_ERROR"
      }
    }
  ]
}
```

### HTTP Error Responses

REST endpoints use standard HTTP codes:
- 200: Success
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

## Future Enhancements

### WebSocket Subscriptions

Add real-time updates for scan progress:

```graphql
subscription {
  scanProgress(jobId: "uuid") {
    processedFiles
    currentFile
    progressPercentage
  }
}
```

### Database Integration

Persist scan jobs and results:

```python
@strawberry.field
def scan_jobs(self, info: Info) -> list[ScanJobType]:
    db = DatabaseService(info.context["config"])
    return db.get_all_scans()
```

### Batch Operations

Support multiple scans in one request:

```graphql
mutation {
  startBatchScan(inputs: [
    { directory: "/videos/set1", scanMode: QUICK },
    { directory: "/videos/set2", scanMode: DEEP }
  ]) {
    jobs {
      id
      status
    }
  }
}
```

### Trakt Integration

Add Trakt.tv operations via GraphQL:

```graphql
mutation {
  syncToTrakt(
    jobId: "uuid"
    watchlist: "main"
    includeStatuses: [HEALTHY]
  ) {
    addedCount
    errors
  }
}
```

## Deployment Notes

### Local Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run with hot reload
make run-api
# or
uvicorn src.api.app:create_app --factory --reload
```

### Docker Deployment

```bash
# Build and run
make docker-api-build
make docker-api

# View logs
docker logs -f cvi-api

# Stop
make docker-api-down
```

### Production Deployment

Recommended setup:

1. **Reverse Proxy**: nginx or Traefik
2. **TLS**: Let's Encrypt certificates
3. **Load Balancer**: For multiple instances
4. **Monitoring**: Prometheus + Grafana
5. **Logging**: Centralized logging (ELK, Loki)

### Environment Variables

Required for production:

```bash
# OIDC Authentication
export OIDC_ENABLED=true
export OIDC_ISSUER=https://auth.example.com
export OIDC_CLIENT_ID=your-client-id
export OIDC_CLIENT_SECRET=your-secret
export OIDC_AUDIENCE=cvi-api

# Optional
export API_HOST=0.0.0.0
export API_PORT=8000
```

## Troubleshooting

### Common Issues

**Problem**: API won't start
- Check config.yaml exists
- Verify dependencies installed
- Check port 8000 availability

**Problem**: GraphQL errors
- Use GraphQL playground to validate syntax
- Check API logs for detailed errors
- Verify field names match schema

**Problem**: Authentication failures
- Ensure OIDC configuration is correct
- Verify JWT token is valid
- Check token expiration

### Debug Mode

Enable debug logging:

```yaml
logging:
  level: DEBUG
```

Or set environment variable:

```bash
export LOG_LEVEL=DEBUG
```

## Contributing

When modifying the API:

1. Update GraphQL schema in `types.py`
2. Implement resolvers in `resolvers.py`
3. Add tests in `tests/unit/test_api.py`
4. Update documentation in `docs/API.md`
5. Add examples if needed
6. Run `make check` before committing

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Strawberry GraphQL](https://strawberry.rocks/)
- [GraphQL Specification](https://spec.graphql.org/)
- [OIDC Specification](https://openid.net/specs/openid-connect-core-1_0.html)
- [Authlib Documentation](https://docs.authlib.org/)

## Change Log

### v1.0.0 (Initial Implementation)

- ✅ FastAPI application with CORS support
- ✅ Strawberry GraphQL schema
- ✅ Query resolvers (scanJobs, scanResults, scanSummary)
- ✅ Mutation resolvers (startScan, generateReport)
- ✅ OIDC authentication framework
- ✅ Docker containerization
- ✅ Comprehensive documentation
- ✅ Usage examples
- ✅ Unit tests

### Future Versions

- [ ] WebSocket subscriptions
- [ ] Database persistence
- [ ] Advanced filtering and pagination
- [ ] Trakt.tv integration
- [ ] Admin dashboard
- [ ] Metrics and monitoring
