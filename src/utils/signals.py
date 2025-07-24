"""
Signal handling utilities.
"""

import logging
import signal
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class SignalManager:
    """Minimal signal manager for graceful shutdown."""

    def __init__(self):
        """Initialize the signal manager."""
        self.shutdown_requested = False
        self.handlers = {}
        logger.debug("SignalManager initialized")

    def register_handler(self, sig: int, handler: Callable) -> None:
        """Register a signal handler."""
        self.handlers[sig] = handler
        signal.signal(sig, self._signal_handler)
        logger.debug(f"Registered handler for signal {sig}")

    def _signal_handler(self, signum: int, frame) -> None:
        """Internal signal handler."""
        logger.info(f"Received signal {signum}")
        self.shutdown_requested = True
        if signum in self.handlers:
            self.handlers[signum](signum, frame)

    def should_shutdown(self) -> bool:
        """Check if shutdown was requested."""
        return self.shutdown_requested

    def reset(self) -> None:
        """Reset shutdown flag."""
        self.shutdown_requested = False