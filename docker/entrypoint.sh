#!/bin/bash
set -e

# Activate poetry environment (if needed)
export PYTHONUNBUFFERED=1

# If a command is passed, run it; otherwise, start a shell
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec bash
fi
