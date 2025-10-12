"""
Web API module for Corrupt Video Inspector.

Provides FastAPI-based REST API and WebSocket endpoints for managing
video scanning operations through a web interface.
"""

from typing import Any

__all__ = ["app", "create_app"]

app: Any = None
create_app: Any = None

try:
    from src.api.main import app, create_app
except ImportError:
    # FastAPI not installed - API module not available
    pass
