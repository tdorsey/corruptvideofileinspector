#!/bin/bash
# Run Ralph iterations - Multiple iterations of autonomous development
#
# This script executes multiple Ralph iterations using GitHub Copilot CLI.
# Ralph will process work items from config/prd.json one at a time,
# making changes and committing them automatically.
#
# Requirements:
# - GitHub Copilot CLI installed and authenticated
# - Ralph submodule initialized at ralph-cli/
# - Valid prd.json configuration
#
# Usage: ./run-ralph-iterations.sh [iterations]
#   iterations: Number of iterations to run (default: 10)

set -euo pipefail

# Nx environment variables (available when run via nx)
WORKSPACE_ROOT="${NX_WORKSPACE_ROOT:-$(git rev-parse --show-toplevel)}"
PROJECT_ROOT="${NX_PROJECT_ROOT:-${WORKSPACE_ROOT}/tools/ralph}"

# Get iteration count from argument or use default
ITERATIONS="${1:-10}"

# Validate iterations is a number
if ! [[ "${ITERATIONS}" =~ ^[0-9]+$ ]]; then
    echo "Error: iterations must be a positive integer"
    echo "Usage: $0 [iterations]"
    exit 1
fi

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
if [ ! -f "ralph-cli/ralph.sh" ]; then
    echo "Error: ralph.sh not found in submodule"
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

echo "=== Running Ralph (${ITERATIONS} iterations) ==="
echo "Workspace: ${WORKSPACE_ROOT}"
echo "Project: ${PROJECT_ROOT}"
echo "Config: config/prd.json"
echo ""

# Execute Ralph's iteration script
# Ralph will use copilot CLI's default model configuration
cd "${WORKSPACE_ROOT}"

# Run iterations
for ((i=1; i<=ITERATIONS; i++)); do
    echo "--- Iteration ${i}/${ITERATIONS} ---"
    "${PROJECT_ROOT}/ralph-cli/ralph-once.sh" || {
        echo "Error: Iteration ${i} failed"
        echo "Stopping iterations"
        exit 1
    }
    echo ""
done

echo "=== All ${ITERATIONS} Ralph iterations complete ==="
echo "Check progress.txt for details"
