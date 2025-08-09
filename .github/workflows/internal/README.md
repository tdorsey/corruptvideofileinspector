# Internal Workflows

This folder contains reusable workflows intended to be called by other workflows only. They are not meant for direct invocation except for testing/debugging.

## Workflows
- `update-pr-labels.yml`: Manages PR labels for automation.
- `get-labels.yml`: Builds and caches label definitions for use in other workflows.

See the main [workflows README](../README.md) for overall structure and guidance.

## Usage Guidelines
- **Do not trigger these workflows manually** except for testing or debugging.
- Always use workflow calls or reusable workflow patterns to invoke these workflows.
- For details on workflow dispatch and calling workflows, see:
  - https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch
  - https://docs.github.com/en/actions/using-workflows/reusing-workflows

## Security Note
Internal workflows may have elevated permissions or perform sensitive operations. Changes should be reviewed by repository maintainers.

---
**Do not add user-facing automation or triggers to this folder.**
