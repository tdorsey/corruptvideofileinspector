"""
Scan summary model for reporting scan results.
"""

from pydantic import BaseModel, Field

from src.core.models.scanning import ScanMode


class ScanSummary(BaseModel):
    """Pydantic model for scan summary results."""

    scan_mode: ScanMode = Field(..., description="Scan mode used")
    processed_files: int = Field(..., description="Total files processed")
    corrupt_files: int = Field(..., description="Number of corrupt files found")
    healthy_files: int = Field(..., description="Number of healthy files")
    deep_scans_needed: int = Field(0, description="Files requiring deep scan (hybrid mode only)")
    deep_scans_completed: int = Field(0, description="Deep scans completed (hybrid mode only)")
    scan_time: float = Field(..., description="Total scan time in seconds")
    success_rate: float = Field(..., description="Success rate percentage")
    was_resumed: bool = Field(False, description="Whether scan was resumed from previous session")
