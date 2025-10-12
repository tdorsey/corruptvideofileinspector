# Nx Troubleshooting Guide

This document provides solutions for common Nx issues in the Corrupt Video Inspector project.

## Project Discovery Issues

### Problem: `nx show projects` returns empty

**Symptoms**:
- `npx nx show projects` produces no output
- `npx nx run cli:test` returns "Cannot find project 'cli'"
- `npm test` returns "No tasks were run"

**Current Status**: 
This is a known issue with the current Nx configuration. Projects are defined in `project.json` files but are not being auto-discovered by Nx.

**Root Cause**:
The exact cause is under investigation. Possible factors:
1. Nx plugin configuration (@nxlv/python) may require specific setup
2. Project.json structure may not match expected format
3. Source code location outside project directories may confuse detection
4. Missing or incorrect executor configuration

**Workaround**:
The CI/CD pipeline uses Make targets directly rather than Nx project commands:
```bash
# Instead of: npx nx run cli:test
# Use: make test

# Instead of: npx nx run cli:lint  
# Use: make lint
```

**Why This Works**:
- Make targets are independent of Nx project discovery
- Nx caching still works through the CI workflow
- All functionality remains available through Make commands

### Investigation Steps Taken

1. ✅ Verified project.json files exist and are valid JSON
2. ✅ Verified nx.json configuration is valid
3. ✅ Tested with and without @nxlv/python plugin
4. ✅ Tried explicit project registration in nx.json
5. ✅ Created workspace.json (deprecated, didn't help)
6. ✅ Reset Nx daemon and cache multiple times
7. ✅ Added package.json to each project directory
8. ✅ Ensured sourceRoot paths are within project directories

### Potential Solutions to Try

1. **Use @nxlv/python generators**:
   ```bash
   npx nx g @nxlv/python:project cli --packageName=corrupt_video_inspector
   ```
   Note: Requires Poetry setup

2. **Simplify project.json**:
   Remove complex executors and use basic structure

3. **Upgrade/downgrade Nx version**:
   Try different Nx versions to find compatible one

4. **Use @nx/workspace plugin**:
   May have better Python support

5. **Create inferred targets**:
   Use Nx plugins that infer targets from existing files (package.json, pyproject.toml)

## CI/CD Issues

### Problem: Cache not restoring in GitHub Actions

**Solution**:
1. Check cache key matches between save and restore:
   ```yaml
   key: nx-cache-${{ runner.os }}-${{ hashFiles('**/package-lock.json', '**/pyproject.toml') }}
   ```

2. Verify cache directory exists:
   ```yaml
   path: .nx/cache
   ```

3. Check workflow logs for cache hit/miss messages

### Problem: "main" branch not found in CI

**Symptoms**:
```
fatal: ambiguous argument 'main': unknown revision or path not in the working tree
```

**Solution**:
Update `defaultBase` in nx.json to match your default branch:
```json
{
  "defaultBase": "main"  // or "master", "develop", etc.
}
```

Or specify base explicitly in commands:
```bash
npx nx affected --target=test --base=origin/main
```

### Problem: Docker layer cache not working

**Solution**:
1. Verify buildx is set up:
   ```yaml
   - uses: docker/setup-buildx-action@v3
   ```

2. Check cache path and keys:
   ```yaml
   - uses: actions/cache@v4
     with:
       path: /tmp/.buildx-cache
       key: ${{ runner.os }}-buildx-${{ hashFiles('**/Dockerfile') }}
   ```

## Local Development Issues

### Problem: Nx commands hang or timeout

**Solution**:
1. Stop the Nx daemon:
   ```bash
   npx nx daemon --stop
   ```

2. Clear all caches:
   ```bash
   npx nx reset
   rm -rf .nx
   ```

3. Restart daemon:
   ```bash
   npx nx daemon --start
   ```

### Problem: Tasks not using cache

**Solution**:
1. Verify caching is enabled in nx.json:
   ```json
   {
     "targetDefaults": {
       "test": {
         "cache": true
       }
     }
   }
   ```

2. Check cache directory exists:
   ```bash
   ls -la .nx/cache
   ```

3. Run with verbose output:
   ```bash
   npx nx run cli:test --verbose
   ```

### Problem: File changes not detected

**Solution**:
1. Ensure daemon is running:
   ```bash
   npx nx daemon --start
   ```

2. Check daemon logs:
   ```bash
   tail -f .nx/workspace-data/d/daemon.log
   ```

3. Force rescan:
   ```bash
   npx nx reset
   ```

## Performance Issues

### Problem: First run is very slow

**Expected Behavior**: 
First run computes dependency graph and executes tasks. Subsequent runs use cache and are much faster.

**Solution**:
Use Nx Cloud for distributed caching:
```bash
npx nx connect-to-nx-cloud
```

### Problem: Large .nx/cache directory

**Solution**:
1. Clean old cache entries:
   ```bash
   npx nx reset
   ```

2. Configure cache size limits in nx.json:
   ```json
   {
     "tasksRunnerOptions": {
       "default": {
         "options": {
           "cacheMaxAge": 7  // days
         }
       }
     }
   }
   ```

## Getting Help

### Debug Information to Collect

When reporting issues, include:

1. **Nx Report**:
   ```bash
   npx nx report
   ```

2. **Project List**:
   ```bash
   npx nx show projects --verbose
   ```

3. **Graph Output**:
   ```bash
   npx nx graph --file=graph.json
   cat graph.json
   ```

4. **Daemon Logs**:
   ```bash
   cat .nx/workspace-data/d/daemon.log
   ```

5. **Configuration**:
   ```bash
   cat nx.json
   cat package.json
   find apps libs -name "project.json"
   ```

### Useful Resources

- [Nx Documentation](https://nx.dev)
- [Nx Discord](https://discord.gg/nx)
- [Nx GitHub Issues](https://github.com/nrwl/nx/issues)
- [@nxlv/python Plugin](https://github.com/lucasvieirasilva/nx-plugins)
- [Project Issues](https://github.com/tdorsey/corruptvideofileinspector/issues)

## Known Limitations

1. **Project Discovery**: Nx CLI commands for specific projects don't work yet
2. **Affected Detection**: Requires proper Git setup and base branch
3. **Python Integration**: Limited compared to TypeScript/JavaScript support
4. **Generator Usage**: Some Nx generators require specific setup (Poetry for Python)

## Success Criteria

The following should work correctly:

- ✅ `make test` - Run tests
- ✅ `make lint` - Lint code
- ✅ `make build` - Build package
- ✅ `npm test` - Run via npm (uses Make)
- ✅ CI/CD pipeline executes successfully
- ✅ Caches persist across CI runs
- ✅ Docker builds succeed
- ⚠️ `npx nx show projects` - Should list projects (currently empty)
- ⚠️ `npx nx run cli:test` - Should run CLI tests (currently fails)
- ⚠️ `npx nx affected` - Should detect changed projects (needs Git setup)

## Future Work

- Resolve project discovery to enable full Nx CLI integration
- Implement proper affected detection in CI
- Add Nx Cloud for distributed caching
- Create custom Nx plugins for Python tooling
- Migrate from Make to pure Nx executors
