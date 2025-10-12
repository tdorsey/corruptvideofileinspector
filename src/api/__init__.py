"""
Web API module for Corrupt Video Inspector.

Provides FastAPI-based REST API and WebSocket endpoints for managing
video scanning operations through a web interface.
"""

__all__ = ["app", "create_app"]

from src.api.main import app, create_app
