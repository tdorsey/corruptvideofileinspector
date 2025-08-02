# Poetry Dynamic Versioning Setup

This project now uses Poetry dynamic versioning to automatically manage version numbers based on Git tags and commits.

## How it Works

### Build System Configuration
The project uses `poetry-dynamic-versioning` as the build backend:

```toml
[build-system]
requires = ["poetry-core>=1.0.0", "poetry-dynamic-versioning>=1.0.0,<2.0.0"]
build-backend = "poetry_dynamic_versioning.backend"
```

### Dynamic Version Configuration
Version numbers are automatically determined from Git tags:

```toml
[tool.poetry-dynamic-versioning]
enable = true
vcs = "git"
style = "semver"
pattern = "default-unprefixed"
metadata = true
tagged-metadata = false
```

## Version Behavior

### Exact Tag Releases
When the current commit has a Git tag (e.g., `v1.0.0`):
- **Version**: `1.0.0`

### Development Versions
When there are commits after the latest tag:
- **Git state**: `v1.0.0-5-g<commit-hash>`
- **Version**: `1.0.1.dev5+g<commit-hash>`

### Fallback Behavior
When the package is not installed (development mode):
- **Version**: `0.0.0+dev`

## Version Access

### Runtime Version Access
```python
from src.version import __version__, get_version

# Get version string
version = get_version()
print(f"Version: {version}")

# Access via module attribute
print(f"Version: {__version__}")
```

### Package Version Access
```python
from src import __version__
print(f"Package version: {__version__}")
```

## Creating Releases

### New Release Process
1. **Create and push a Git tag**:
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

2. **Build the package**:
   ```bash
   poetry build
   ```

3. **The version will automatically be `1.1.0`**

### Development Builds
- No special steps needed
- Version automatically includes development metadata
- Example: `1.1.1.dev3+g<commit-hash>`

## Benefits

1. **No manual version updates**: Version is automatically derived from Git tags
2. **Consistent versioning**: Follows semantic versioning standards
3. **Development tracking**: Development versions include commit information
4. **Build reproducibility**: Version includes Git metadata for traceability

## Dependencies

The dynamic versioning adds these dependencies:
- `poetry-dynamic-versioning` (build-time)
- `importlib_metadata` (runtime, Python < 3.8 only)

## Testing

Run the version tests to verify functionality:
```bash
python -m pytest tests/test_version.py -v
```

Run the demo script to see versioning in action:
```bash
python demo_versioning.py
```