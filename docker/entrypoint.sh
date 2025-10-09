#!/bin/bash
set -e

# Default PUID and PGID to 1000 if not set
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Get the current user and group ID
CURRENT_UID=$(id -u inspector)
CURRENT_GID=$(id -g inspector)

# Only modify user/group if PUID/PGID differ from current values
if [ "$PUID" != "$CURRENT_UID" ] || [ "$PGID" != "$CURRENT_GID" ]; then
    echo "Setting up user with PUID=$PUID and PGID=$PGID"
    
    # Modify group ID if needed
    if [ "$PGID" != "$CURRENT_GID" ]; then
        groupmod -o -g "$PGID" inspector
    fi
    
    # Modify user ID if needed
    if [ "$PUID" != "$CURRENT_UID" ]; then
        usermod -o -u "$PUID" inspector
    fi
    
    # Fix ownership of app directories
    chown -R inspector:inspector /app/videos /app/output /app/logs 2>/dev/null || true
fi

# Activate poetry environment (if needed)
export PYTHONUNBUFFERED=1

# Switch to inspector user and run command
if [ "$#" -gt 0 ]; then
    exec gosu inspector "$@"
else
    exec gosu inspector bash
fi
