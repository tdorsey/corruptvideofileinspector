"""
Progress reporting utilities.
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ProgressReporter:
    """Minimal progress reporter for scan operations."""

    def __init__(self, total: int = 0, callback: Optional[Callable] = None):
        """Initialize the progress reporter."""
        self.total = total
        self.current = 0
        self.callback = callback
        logger.debug(f"ProgressReporter initialized with total: {total}")

    def update(self, increment: int = 1, message: str = "") -> None:
        """Update progress."""
        self.current += increment
        logger.debug(f"Progress: {self.current}/{self.total} - {message}")
        if self.callback:
            self.callback(self.current, self.total, message)

    def finish(self) -> None:
        """Mark progress as finished."""
        logger.debug("Progress finished")
        if self.callback:
            self.callback(self.total, self.total, "Complete")