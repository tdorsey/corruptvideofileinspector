---
name: docker-debug
description: Skill for debugging Docker containers, diagnosing failures, and resolving container issues
---

# Docker Debug Skill

This skill provides systematic procedures for diagnosing and resolving Docker container failures, compose service issues, and runtime errors.

## When to Use

- A container is crashing, restarting, or failing health checks
- A service is unreachable or behaving unexpectedly
- You need to inspect environment variables or mounted files inside a running container
- A build is failing and you need to identify the root cause
- Container logs show errors that need investigation

## Diagnostic Commands

### Inspect Container State

```bash
# List all containers including stopped ones
docker ps -a

# Detailed inspection of a specific container
docker inspect <container_name_or_id>

# Check container exit code and last error
docker inspect <container> --format '{{.State.ExitCode}} {{.State.Error}}'
```

### Log Analysis

```bash
# Tail logs for a running service
docker logs <container> --tail 100 -f

# Logs since a timestamp
docker logs <container> --since 10m

# Compose service logs (all services)
docker compose logs --tail 50

# Compose logs for one service
docker compose logs <service> --tail 100 -f
```

### Enter a Running Container

```bash
# Interactive shell (prefer bash, fall back to sh)
docker exec -it <container> bash
docker exec -it <container> sh

# Run a single diagnostic command non-interactively
docker exec <container> env
docker exec <container> cat /etc/hosts
docker exec <container> ls -la /app
```

### Network Diagnostics

```bash
# List networks
docker network ls

# Inspect a network to see connected containers and IP assignments
docker network inspect <network_name>

# Test connectivity between services (from inside a container)
docker exec <container> ping <other_service>
docker exec <container> curl -sf http://<service>:<port>/health
```

### Volume and File Inspection

```bash
# List volumes
docker volume ls

# Inspect a volume (mountpoint on host)
docker volume inspect <volume_name>

# Check file permissions inside container
docker exec <container> ls -la /path/to/mount
```

## Common Issues and Remedies

### Container Exits Immediately

1. Check exit code: `docker inspect <container> --format '{{.State.ExitCode}}'`
2. Read logs: `docker logs <container>`
3. Common causes:
   - Missing required environment variable → add to compose env or `.env`
   - Entrypoint script error → exec into image directly: `docker run --entrypoint sh -it <image>`
   - Missing file or wrong path → verify volume mounts

### Health Check Failing

```bash
# See health check history
docker inspect <container> --format '{{json .State.Health}}' | jq .

# Run the health check command manually inside the container
docker exec <container> <healthcheck_command>
```

### Port Already in Use

```bash
# Find what process owns the port
sudo lsof -i :<port>
sudo ss -tlnp | grep :<port>
```

### Permission Denied on Volume Mount

```bash
# Check UID/GID inside container
docker exec <container> id

# Fix ownership on the host path
sudo chown -R <uid>:<gid> /host/path
```

### Out of Disk Space

```bash
# Show Docker disk usage
docker system df

# Clean up stopped containers, dangling images, unused networks and build cache
docker system prune

# Also remove unused volumes (destructive — confirm first)
docker system prune --volumes
```

## Compose-Specific Debugging

```bash
# Validate compose file syntax
docker compose config

# Rebuild a specific service without cache
docker compose build --no-cache <service>

# Restart a single service
docker compose restart <service>

# Recreate a service (picks up env/config changes)
docker compose up -d --force-recreate <service>

# Scale down then up to reset state
docker compose stop <service> && docker compose up -d <service>
```

## Build Failure Debugging

```bash
# Build with full output (no cache) to see every layer
docker build --no-cache --progress=plain -t debug-image .

# Checkpoint at a failing layer: comment out subsequent lines in Dockerfile,
# build, exec in, then investigate interactively
docker run --rm -it debug-image sh
```

## Environment Variable Verification

```bash
# Dump all env vars inside a container
docker exec <container> env | sort

# Check a specific variable
docker exec <container> printenv MY_VAR
```

## Definition of Done

- Container is running and healthy (`docker ps` shows `healthy` or no health check configured)
- No ERROR-level log lines in `docker logs` output
- Service endpoints respond correctly
- Root cause is identified and documented if a workaround was applied
