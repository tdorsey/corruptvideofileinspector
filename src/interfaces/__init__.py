"""
Interface abstractions for decoupling presentation layers from core business logic.

This module provides abstract interfaces that any presentation layer (CLI, web API, GUI)
can implement to interact with the core video corruption detection functionality.

The interfaces support:
- Configuration provision from any source (CLI args, files, API requests, etc.)
- Result handling for any output format or destination
- Error handling appropriate for any interface type
- Progress reporting for any UI paradigm
"""

from .base import (
    ConfigurationProvider,
    ErrorHandler,
    ProgressReporter,
    ResultHandler,
)
from .factory import InterfaceFactory

__all__ = [
    "ConfigurationProvider",
    "ErrorHandler", 
    "ProgressReporter",
    "ResultHandler",
    "InterfaceFactory",
]