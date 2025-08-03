# Corrupt Video Inspector – Project Instructions

## Overview
This project is a containerized Python application for scanning directories for corrupt video files, generating reports, and syncing results to Trakt.tv. It uses `pyproject.toml` for configuration, Docker/Docker Compose for development, and the Click framework for CLI commands.

---

## Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Python 3.13+ (for local development outside containers)
- (Optional) Trakt.tv API credentials for Trakt integration

### Setup
1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd corruptvideofileinspector
   ```
2. **Copy and configure environment variables:**
   - Copy `.env.example` to `.env` and fill in required values.
   - For Trakt integration, place secrets in `docker/secrets/` as documented.

3. **Build and start containers:**
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```
   For development:
   ```bash
   docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up
   ```

---

## CLI Usage

Run the CLI via Docker (recommended):
```bash
docker-compose run --rm app corrupt-video-inspector --help
```
Or locally (if dependencies are installed):
```bash
python -m src --help
```

### Main Commands
- `scan` – Scan a directory for corrupt video files
- `list-files` – List all video files in a directory
- `trakt sync` – Sync scan results to Trakt.tv
- `report` – Generate a report from scan results
- `test-ffmpeg` – Test FFmpeg installation
- `show-config` – Show current configuration

All commands support the global `--config` option for specifying a config file.

---

## Development

- **Code style:**
  - All code must have type annotations.
  - Use f-strings for formatting.
  - Line length ≤ 79 characters.
  - Imports must be sorted and grouped (standard library, third-party, local).
  - Run `make lint-fix` to auto-fix style issues.
- **Testing:**
  - Run tests in the container:
    ```bash
    docker-compose run --rm app python -m pytest
    ```
- **Type checking:**
  - Run mypy in the container if configured.
- **Linting:**
  - Run `make lint` or use the containerized linter.

---

## Configuration
- Main config file: `config.yaml` (default, override with `--config`)
- Environment variables: see `.env.example`
- Secrets: never commit secrets, use Docker secrets or environment variables

---

## Contributing
- Follow [Conventional Commits](https://www.conventionalcommits.org/)
- Document new environment variables in `.env.example`
- Update documentation for any configuration or CLI changes
- Always develop and test in containers
- Always fix lint issues when they are reported

---

## Troubleshooting
- Use `docker compose logs` for debugging
- Check volume mounts if code changes are not reflected
- Ensure all required environment variables are set
- For FFmpeg issues, use `test-ffmpeg` command

---

## Security & Best Practices
- Never commit secrets
- Use non-root users in production containers
- Regularly audit dependencies (`pip-audit`)
- Validate all input and configuration

---

## License
See `LICENSE` file for details.
