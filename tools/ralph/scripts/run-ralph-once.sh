#!/bin/bash
# Run Ralph once - Single iteration of autonomous development
#
# This script executes a single Ralph iteration using GitHub Copilot CLI.
# Ralph will process one work item from config/prd.json, make changes,
# and commit them automatically.
#
# Requirements:
# - GitHub Copilot CLI installed and authenticated
# - Ralph submodule initialized at ralph-cli/
# - Valid prd.json configuration
#
# Usage: ./run-ralph-once.sh

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

# Verify Ralph's main script exists
if [ ! -f "ralph-cli/ralph-once.sh" ]; then
    echo "Error: ralph-once.sh not found in submodule"
    echo "Please check that the submodule is properly initialized"
    exit 1
fi

# Verify copilot CLI is available
if ! command -v copilot &> /dev/null; then
    echo "Error: GitHub Copilot CLI not found"
    echo "Please install Copilot CLI: https://githubnext.com/projects/copilot-cli"
    exit 1
fi

# Verify prd.json exists
if [ ! -f "config/prd.json" ]; then
    echo "Error: config/prd.json not found"
    echo "Please create a configuration file with work items"
    exit 1
fi

echo "=== Running Ralph (Single Iteration) ==="
echo "Workspace: ${WORKSPACE_ROOT}"
echo "Project: ${PROJECT_ROOT}"
echo "Config: config/prd.json"
echo ""

# Execute Ralph's single iteration script
# Ralph will use copilot CLI's default model configuration
cd "${WORKSPACE_ROOT}"
"${PROJECT_ROOT}/ralph-cli/ralph-once.sh"

echo ""
echo "=== Ralph iteration complete ==="
echo "Check progress.txt for details"
