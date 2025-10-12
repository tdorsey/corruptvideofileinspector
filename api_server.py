#!/usr/bin/env python3
"""
API server entry point for Corrupt Video Inspector web interface.
"""

import logging
import sys
from pathlib import Path

# Ensure src is in Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    import uvicorn

    from src.api.main import app

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )
