"""REST API endpoints for scan operations."""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from src.api.graphql.resolvers import (
    _scan_jobs,
    _scan_results,
    convert_scan_mode,
)
from src.api.graphql.types import ScanModeType
from src.cli.handlers import ScanHandler
from src.config import load_config
from src.core.models.scanning import ScanProgress

logger = logging.getLogger(__name__)


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for scan progress updates."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        """Connect a client to a specific job's updates."""
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logger.info(f"WebSocket connected for job {job_id}")

    def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        """Disconnect a client from job updates."""
        if job_id in self.active_connections:
            self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
        logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_progress(self, job_id: str, progress: dict[str, Any]) -> None:
        """Send progress update to all connected clients for a job."""
        if job_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(progress)
                except Exception:
                    logger.exception("Error sending progress")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(job_id, connection)


manager = ConnectionManager()


# Pydantic models for REST API
class ScanRequest(BaseModel):
    """Request model for starting a scan."""

    directory: str = Field(..., description="Directory path to scan")
    scan_mode: str = Field(default="quick", description="Scan mode: quick, deep, or hybrid")
    recursive: bool = Field(default=True, description="Scan subdirectories recursively")
    resume: bool = Field(default=True, description="Resume from previous scan if available")


class ScanResponse(BaseModel):
    """Response model for scan operations."""

    id: str = Field(..., description="Unique scan job ID")
    directory: str = Field(..., description="Directory being scanned")
    scan_mode: str = Field(..., description="Scan mode used")
    status: str = Field(..., description="Current status: running, completed, failed")
    started_at: datetime = Field(..., description="Scan start time")
    completed_at: datetime | None = Field(None, description="Scan completion time")
    results_count: int = Field(default=0, description="Number of results")


class ProgressUpdate(BaseModel):
    """Progress update model."""

    current_file: str = Field(..., description="Current file being processed")
    processed_files: int = Field(..., description="Number of files processed")
    total_files: int = Field(..., description="Total files to process")
    progress_percentage: float = Field(..., description="Progress percentage")
    corrupt_count: int = Field(default=0, description="Number of corrupt files found")
    healthy_count: int = Field(default=0, description="Number of healthy files found")


# Create router
router = APIRouter()


@router.post("/api/scans", response_model=ScanResponse)
async def create_scan(request: ScanRequest) -> ScanResponse:
    """Start a new video scan operation."""
    config = load_config()
    job_id = str(uuid.uuid4())

    # Validate scan mode
    def _validate_scan_mode(mode: str) -> ScanModeType:
        """Validate and convert scan mode string to enum."""
        mode_lower = mode.lower()
        if mode_lower == "quick":
            return ScanModeType.QUICK
        if mode_lower == "deep":
            return ScanModeType.DEEP
        if mode_lower == "hybrid":
            return ScanModeType.HYBRID
        raise ValueError(f"Invalid scan mode: {mode}")

    try:
        scan_mode_type = _validate_scan_mode(request.scan_mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Create scan job record
    _scan_jobs[job_id] = {
        "directory": request.directory,
        "scan_mode": scan_mode_type,
        "status": "running",
        "started_at": datetime.now(),
    }

    # Define progress callback for WebSocket updates
    async def progress_callback(progress: ScanProgress) -> None:
        """Send progress updates via WebSocket."""
        healthy_count = progress.processed_count - progress.corrupt_count
        progress_data = {
            "current_file": progress.current_file or "",
            "processed_files": progress.processed_count,
            "total_files": progress.total_files,
            "progress_percentage": (
                (progress.processed_count / progress.total_files * 100)
                if progress.total_files > 0
                else 0
            ),
            "corrupt_count": progress.corrupt_count,
            "healthy_count": max(0, healthy_count),
        }
        await manager.send_progress(job_id, progress_data)

    try:
        # Initialize scan handler
        scan_handler = ScanHandler(config)

        # Run the scan (this is blocking, in production use background tasks)
        summary = scan_handler.run_scan(
            directory=Path(request.directory),
            scan_mode=convert_scan_mode(scan_mode_type),
            recursive=request.recursive,
            resume=request.resume,
        )

        # Update job with results
        _scan_jobs[job_id]["status"] = "completed"
        _scan_jobs[job_id]["completed_at"] = datetime.now()
        if summary:
            _scan_jobs[job_id]["summary"] = summary
            _scan_results[job_id] = []

        # Send final progress update
        if summary:
            await manager.send_progress(
                job_id,
                {
                    "current_file": "Complete",
                    "processed_files": summary.processed_files,
                    "total_files": summary.total_files,
                    "progress_percentage": 100.0,
                    "corrupt_count": summary.corrupt_files,
                    "healthy_count": summary.healthy_files,
                    "status": "completed",
                },
            )

    except Exception as e:
        logger.exception("Scan failed")
        _scan_jobs[job_id]["status"] = "failed"
        _scan_jobs[job_id]["completed_at"] = datetime.now()
        _scan_jobs[job_id]["error"] = str(e)

        # Send error update
        await manager.send_progress(
            job_id, {"status": "failed", "error": str(e), "progress_percentage": 0}
        )

    job_data = _scan_jobs[job_id]
    return ScanResponse(
        id=job_id,
        directory=job_data["directory"],
        scan_mode=job_data["scan_mode"].value,
        status=job_data["status"],
        started_at=job_data["started_at"],
        completed_at=job_data.get("completed_at"),
        results_count=len(_scan_results.get(job_id, [])),
    )


@router.get("/api/scans", response_model=list[ScanResponse])
async def list_scans() -> list[ScanResponse]:
    """Get all scan jobs."""
    scans = []
    for job_id, job_data in _scan_jobs.items():
        scans.append(
            ScanResponse(
                id=job_id,
                directory=job_data["directory"],
                scan_mode=job_data["scan_mode"].value,
                status=job_data["status"],
                started_at=job_data["started_at"],
                completed_at=job_data.get("completed_at"),
                results_count=len(_scan_results.get(job_id, [])),
            )
        )
    return scans


@router.get("/api/scans/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str) -> ScanResponse:
    """Get a specific scan job by ID."""
    job_data = _scan_jobs.get(scan_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanResponse(
        id=scan_id,
        directory=job_data["directory"],
        scan_mode=job_data["scan_mode"].value,
        status=job_data["status"],
        started_at=job_data["started_at"],
        completed_at=job_data.get("completed_at"),
        results_count=len(_scan_results.get(scan_id, [])),
    )


@router.websocket("/ws/scans/{scan_id}")
async def websocket_scan_progress(websocket: WebSocket, scan_id: str) -> None:
    """WebSocket endpoint for real-time scan progress updates."""
    await manager.connect(scan_id, websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            # Echo back for testing
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(scan_id, websocket)
        logger.info(f"Client disconnected from scan {scan_id}")
