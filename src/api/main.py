"""
FastAPI application for Corrupt Video Inspector web interface.
"""

import asyncio
import contextlib
import logging
import uuid
from pathlib import Path
from shutil import which
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.api.models import (
    DatabaseStatsResponse,
    HealthResponse,
    ScanRequest,
    ScanResponse,
    ScanResultsResponse,
    ScanStatusEnum,
    ScanStatusResponse,
)
from src.config import load_config
from src.core.models.scanning import ScanProgress, ScanSummary
from src.core.scanner import VideoScanner
from src.version import __version__

logger = logging.getLogger(__name__)

# Global scan state management
active_scans: dict[str, dict[str, Any]] = {}


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Corrupt Video Inspector API",
        description="REST API for video file corruption detection",
        version=__version__,
    )

    # CORS middleware for frontend access
    # Note: In production, configure allowed origins explicitly
    # For development, we allow localhost origins
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.get("/api/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        try:
            ffmpeg_available = which("ffmpeg") is not None
            return HealthResponse(
                status="healthy",
                version=__version__,
                ffmpeg_available=ffmpeg_available,
            )
        except Exception:
            logger.exception("Health check failed")
            raise HTTPException(
                status_code=500, detail="Internal server error during health check"
            ) from None

    def _validate_directory(directory: Path) -> None:
        """Validate directory path and prevent path traversal attacks."""
        # Resolve to absolute path to prevent directory traversal
        try:
            resolved_path = directory.resolve()
        except (OSError, RuntimeError) as e:
            logger.warning(f"Failed to resolve directory path: {e}")
            raise HTTPException(status_code=400, detail="Invalid directory path") from None

        # Check if path exists
        if not resolved_path.exists():
            raise HTTPException(status_code=400, detail="Directory does not exist")

        # Check if it's a directory
        if not resolved_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        # Additional security: ensure path is absolute and doesn't contain suspicious patterns
        path_str = str(resolved_path)
        if ".." in path_str or path_str.startswith("~"):
            raise HTTPException(status_code=400, detail="Invalid directory path")

    @app.post("/api/scans", response_model=ScanResponse)
    async def start_scan(request: ScanRequest) -> ScanResponse:
        """Start a new video scan."""
        try:
            # Validate directory exists
            directory = Path(request.directory)
            _validate_directory(directory)

            # Generate unique scan ID
            scan_id = str(uuid.uuid4())

            # Initialize scan state
            active_scans[scan_id] = {
                "status": ScanStatusEnum.PENDING,
                "directory": str(directory),
                "mode": request.mode.value,
                "recursive": request.recursive,
                "max_workers": request.max_workers,
                "progress": {},
                "results": None,
                "error": None,
            }

            # Start scan in background (task reference kept to prevent GC)
            _ = asyncio.create_task(run_scan(scan_id, request))  # noqa: RUF006

            return ScanResponse(
                scan_id=scan_id,
                status=ScanStatusEnum.PENDING,
                message="Scan started successfully",
            )

        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to start scan")
            raise HTTPException(
                status_code=500, detail="Internal server error starting scan"
            ) from None

    @app.get("/api/scans/{scan_id}", response_model=ScanStatusResponse)
    async def get_scan_status(scan_id: str) -> ScanStatusResponse:
        """Get status of a specific scan."""
        if scan_id not in active_scans:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan_data = active_scans[scan_id]
        return ScanStatusResponse(
            scan_id=scan_id,
            status=scan_data["status"],
            directory=scan_data["directory"],
            mode=scan_data["mode"],
            progress=scan_data["progress"],
            results=scan_data["results"],
            error=scan_data["error"],
        )

    @app.get("/api/scans/{scan_id}/results", response_model=ScanResultsResponse)
    async def get_scan_results(scan_id: str) -> ScanResultsResponse:
        """Get results of a completed scan."""
        if scan_id not in active_scans:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan_data = active_scans[scan_id]
        if scan_data["status"] != ScanStatusEnum.COMPLETED:
            raise HTTPException(status_code=400, detail="Scan not completed")

        if scan_data["results"] is None:
            raise HTTPException(status_code=404, detail="Results not available")

        results = scan_data["results"]
        return ScanResultsResponse(
            scan_id=scan_id, results=results["details"], summary=results["summary"]
        )

    @app.delete("/api/scans/{scan_id}")
    async def cancel_scan(scan_id: str) -> dict[str, str]:
        """Cancel a running scan."""
        if scan_id not in active_scans:
            raise HTTPException(status_code=404, detail="Scan not found")

        scan_data = active_scans[scan_id]
        if scan_data["status"] == ScanStatusEnum.RUNNING:
            scan_data["status"] = ScanStatusEnum.CANCELLED
            scan_data["error"] = "Scan cancelled by user"
            return {"message": "Scan cancelled successfully"}
        raise HTTPException(
            status_code=400, detail=f"Cannot cancel scan in {scan_data['status']} state"
        )

    @app.get("/api/database/stats", response_model=DatabaseStatsResponse)
    async def get_database_stats() -> DatabaseStatsResponse:
        """Get database statistics."""
        # Placeholder - will be implemented with database integration
        return DatabaseStatsResponse(
            total_files=0,
            healthy_files=0,
            corrupt_files=0,
            suspicious_files=0,
            last_scan_time=None,
        )

    @app.websocket("/ws/scans/{scan_id}")
    async def websocket_scan_progress(websocket: WebSocket, scan_id: str) -> None:
        """WebSocket endpoint for real-time scan progress."""
        await websocket.accept()

        try:
            # Check if scan exists
            if scan_id not in active_scans:
                await websocket.send_json({"type": "error", "data": {"message": "Scan not found"}})
                await websocket.close()
                return

            # Send initial status
            scan_data = active_scans[scan_id]
            await websocket.send_json(
                {"type": "status", "data": {"status": scan_data["status"].value}}
            )

            # Stream progress updates while scan is running
            while scan_data["status"] in [ScanStatusEnum.PENDING, ScanStatusEnum.RUNNING]:
                await websocket.send_json({"type": "progress", "data": scan_data["progress"]})
                await asyncio.sleep(0.5)  # Update every 500ms

            # Send final status
            await websocket.send_json(
                {
                    "type": "complete",
                    "data": {
                        "status": scan_data["status"].value,
                        "error": scan_data["error"],
                    },
                }
            )

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for scan {scan_id}")
        except Exception:
            logger.exception("WebSocket error")
            with contextlib.suppress(Exception):
                await websocket.send_json(
                    {"type": "error", "data": {"message": "Internal server error"}}
                )

    return app


async def run_scan(scan_id: str, request: ScanRequest) -> None:
    """Run video scan in background task."""
    scan_data = active_scans[scan_id]

    try:
        scan_data["status"] = ScanStatusEnum.RUNNING

        # Load configuration
        config = load_config()

        # Override with request parameters
        config.processing.max_workers = request.max_workers
        config.scan.recursive = request.recursive
        # mode is ScanMode enum, no need to convert to string
        config.processing.default_mode = request.mode.value

        # Create scanner
        scanner = VideoScanner(config)

        # Progress callback
        def progress_callback(progress: ScanProgress) -> None:
            scan_data["progress"] = progress.model_dump()

        # Run scan
        directory = Path(request.directory)
        summary: ScanSummary | None = scanner.scan_directory(
            directory=directory,
            scan_mode=request.mode,
            recursive=request.recursive,
            progress_callback=progress_callback,
        )

        if summary is None:
            scan_data["status"] = ScanStatusEnum.FAILED
            scan_data["error"] = "Scan completed with no results"
        else:
            scan_data["status"] = ScanStatusEnum.COMPLETED
            # Store summary data - individual file results not available from scan_directory
            scan_data["results"] = {
                "summary": summary.model_dump(),
                "details": [],  # TODO: Implement file-level results storage
            }

    except Exception:
        logger.exception(f"Scan {scan_id} failed")
        scan_data["status"] = ScanStatusEnum.FAILED
        scan_data["error"] = "Scan failed due to an internal error"


# Create app instance
app = create_app()
