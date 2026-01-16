# Ralph Submodule Setup Instructions

This document provides step-by-step instructions for adding the Ralph submodule to the repository. The submodule could not be added automatically during initial integration due to GitHub CLI authentication requirements.

## Prerequisites

Before proceeding, ensure you have:

1. **GitHub CLI (gh) installed and authenticated**
   ```bash
   gh auth status
   ```
   If not authenticated, run: `gh auth login`

2. **Write access to the TDorsey/corruptvideoinspector repository**

3. **Working directory is clean**
   ```bash
   git status
   # Should show "working tree clean"
   ```

## Step 1: Fork Ralph Repository (If Not Already Done)

Check if TDorsey/ralph exists:
```bash
gh repo view TDorsey/ralph 2>/dev/null && echo "✅ Fork exists" || echo "❌ Fork needed"
```

If the fork doesn't exist, create it:
```bash
# Fork soderlind/ralph to TDorsey/ralph
gh repo fork soderlind/ralph --clone=false --remote=false --org TDorsey
```

## Step 2: Get Latest Release Tag

Fetch the latest release tag from TDorsey/ralph:
```bash
LATEST_TAG=$(gh release view --repo TDorsey/ralph --json tagName -q .tagName)
echo "Latest release: ${LATEST_TAG}"
```

If no releases exist yet, you can use soderlind/ralph instead:
```bash
LATEST_TAG=$(gh release view --repo soderlind/ralph --json tagName -q .tagName)
echo "Latest release from upstream: ${LATEST_TAG}"
```

## Step 3: Add Ralph Submodule

Add Ralph as a submodule:
```bash
# Ensure you're in the repository root
cd /path/to/corruptvideoinspector

# Add submodule (adjust URL if using soderlind/ralph instead)
git submodule add https://github.com/TDorsey/ralph.git tools/ralph/ralph-cli
```

## Step 4: Pin Submodule to Release Tag

Pin the submodule to the latest release tag (not branch HEAD):
```bash
cd tools/ralph/ralph-cli

# Fetch all tags
git fetch --tags

# Checkout the release tag
git checkout ${LATEST_TAG}

# Verify you're on a tag
git describe --tags --exact-match
# Should output: <release-tag>

# Return to repository root
cd ../../..
```

## Step 5: Commit Submodule

Commit the submodule reference:
```bash
# Check what will be committed
git status
# Should show: new file: tools/ralph/ralph-cli (and possibly .gitmodules)

# Add the submodule
git add .gitmodules tools/ralph/ralph-cli

# Commit with conventional commit format
git commit -m "feat(ralph): add ralph submodule pinned to ${LATEST_TAG}"
```

## Step 6: Verify Setup

Verify the submodule is correctly configured:
```bash
# Check submodule status
git submodule status
# Should show: <commit-hash> tools/ralph/ralph-cli (<tag-name>)

# Verify files exist
ls -la tools/ralph/ralph-cli/
# Should show ralph.sh, ralph-once.sh, and other Ralph files

# Verify Nx can see the project
nx show project ralph
```

## Step 7: Test Ralph Integration

Test that Ralph integration works (requires Copilot CLI):
```bash
# Verify copilot CLI is available
copilot --version

# Test single iteration (will fail gracefully if no work items)
nx run ralph:once

# Check that scripts are executable
ls -l tools/ralph/scripts/*.sh
# Should show -rwxr-xr-x permissions
```

## Step 8: Push Changes

Push the submodule to the remote repository:
```bash
# Push to main (or your feature branch)
git push origin main
```

## Verification Checklist

After completing setup, verify:

- [ ] Submodule exists at `tools/ralph/ralph-cli`
- [ ] Submodule is pinned to a release tag (check with `cd tools/ralph/ralph-cli && git describe --tags --exact-match`)
- [ ] `.gitmodules` file exists and references the submodule
- [ ] `git submodule status` shows the tag name in parentheses
- [ ] Nx recognizes the ralph project (`nx show project ralph`)
- [ ] Scripts are executable (`ls -l tools/ralph/scripts/*.sh`)

## Troubleshooting

### "fatal: remote error: Repository not found"

The TDorsey/ralph repository may not exist. Options:
1. Fork soderlind/ralph to TDorsey/ralph using `gh repo fork`
2. Use soderlind/ralph directly: `git submodule add https://github.com/soderlind/ralph.git tools/ralph/ralph-cli`

### "fatal: 'tools/ralph/ralph-cli' already exists in the index"

The submodule path is already tracked. Remove it first:
```bash
git rm -r tools/ralph/ralph-cli
git commit -m "chore(ralph): remove incorrect submodule"
# Then retry from Step 3
```

### Submodule shows modified after checkout

Ensure you committed the submodule reference after checking out the tag:
```bash
cd tools/ralph/ralph-cli
git status
# If clean, return to root and check
cd ../../..
git status
# If tools/ralph/ralph-cli shows as modified, add and commit
git add tools/ralph/ralph-cli
git commit -m "fix(ralph): update submodule reference to release tag"
```

### CI fails with "Ralph submodule is not pinned to a release tag"

The submodule is on a branch HEAD instead of a release tag. Fix:
```bash
cd tools/ralph/ralph-cli
git fetch --tags
LATEST_TAG=$(git describe --tags $(git rev-list --tags --max-count=1))
git checkout ${LATEST_TAG}
cd ../../..
git add tools/ralph/ralph-cli
git commit -m "fix(ralph): pin submodule to release tag ${LATEST_TAG}"
git push
```

## Alternative: Manual Clone (Not Recommended)

If you cannot use submodules, you can manually clone Ralph (not recommended as it loses version tracking):

```bash
# Clone Ralph manually
git clone https://github.com/TDorsey/ralph.git tools/ralph/ralph-cli

# Checkout release tag
cd tools/ralph/ralph-cli
LATEST_TAG=$(git describe --tags $(git rev-list --tags --max-count=1))
git checkout ${LATEST_TAG}

# Remove .git to avoid nested repository issues
rm -rf .git

# Return and commit
cd ../../..
git add tools/ralph/ralph-cli
git commit -m "feat(ralph): add ralph cli at release ${LATEST_TAG}"
```

**Warning**: This approach loses the ability to update Ralph using `nx run ralph:update` and makes version tracking more difficult.

## Next Steps

After successfully adding the submodule:

1. **Read the documentation**: `cat tools/ralph/README.md`
2. **Edit work items**: `vim tools/ralph/config/prd.json`
3. **Run Ralph**: `nx run ralph:once`
4. **Monitor progress**: `cat tools/ralph/progress.txt`

## Support

For issues with:
- **Submodule setup**: Open issue in corruptvideoinspector repository
- **Ralph functionality**: Open issue in TDorsey/ralph or soderlind/ralph repository
- **GitHub CLI**: See https://cli.github.com/manual/

## References

- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Ralph Tool Documentation](README.md)
- [Nx Workspace Documentation](https://nx.dev)
