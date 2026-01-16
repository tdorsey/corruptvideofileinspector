#!/bin/bash
# Update Ralph submodule to latest release
#
# This script updates the Ralph submodule to the latest release tag
# from the TDorsey/ralph repository.
#
# Requirements:
# - Git with submodule support
# - GitHub CLI (gh) for fetching release information
# - Ralph submodule initialized at ralph-cli/
#
# Usage: ./update-ralph.sh

set -euo pipefail

# Nx environment variables (available when run via nx)
WORKSPACE_ROOT="${NX_WORKSPACE_ROOT:-$(git rev-parse --show-toplevel)}"
PROJECT_ROOT="${NX_PROJECT_ROOT:-${WORKSPACE_ROOT}/tools/ralph}"

# Change to project root
cd "${PROJECT_ROOT}"

# Verify Ralph submodule exists
if [ ! -d "ralph-cli" ]; then
    echo "Error: Ralph submodule not found at ralph-cli/"
    echo "Please initialize the submodule first:"
    echo "  git submodule update --init --recursive"
    exit 1
fi

# Verify gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) not found"
    echo "Please install gh CLI: https://cli.github.com/"
    exit 1
fi

echo "=== Updating Ralph to latest release ==="
echo "Workspace: ${WORKSPACE_ROOT}"
echo "Project: ${PROJECT_ROOT}"
echo ""

# Get current submodule version
cd ralph-cli
CURRENT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "not on a tag")
echo "Current version: ${CURRENT_TAG}"

# Get latest release tag from TDorsey/ralph
echo "Fetching latest release from TDorsey/ralph..."
LATEST_TAG=$(gh release view --repo TDorsey/ralph --json tagName -q .tagName)

if [ -z "${LATEST_TAG}" ]; then
    echo "Error: Could not fetch latest release tag"
    exit 1
fi

echo "Latest release: ${LATEST_TAG}"

# Check if already on latest
if [ "${CURRENT_TAG}" = "${LATEST_TAG}" ]; then
    echo "Already on latest release (${LATEST_TAG})"
    exit 0
fi

# Update to latest release
echo "Updating submodule to ${LATEST_TAG}..."
git fetch --tags
git checkout "${LATEST_TAG}"

# Return to project root
cd "${PROJECT_ROOT}"

echo ""
echo "=== Ralph updated successfully ==="
echo "Updated from ${CURRENT_TAG} to ${LATEST_TAG}"
echo ""
echo "To commit this update:"
echo "  git add tools/ralph/ralph-cli"
echo "  git commit -m \"chore(ralph): update submodule to ${LATEST_TAG}\""
