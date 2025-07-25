"""Entry point for running corrupt-video-inspector as a module.

This allows the package to be executed as:
    python -m corrupt_video_inspector
"""

from __future__ import annotations

import sys

from corrupt_video_inspector.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
