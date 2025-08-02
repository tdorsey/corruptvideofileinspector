from enum import Enum
from typing import ClassVar, Optional

from pydantic import BaseModel, Field


class ScanMode(str, Enum):
    QUICK = "quick"
    DEEP = "deep"
    HYBRID = "hybrid"


class ScanOutputModel(BaseModel):
    scan_mode: ScanMode = Field(..., description="Type of scan performed")
    total_files: int = Field(..., description="Total number of files found")
    processed_files: int = Field(..., description="Number of files processed")
    corrupt_files: int = Field(..., description="Number of corrupt files found")
    healthy_files: int = Field(..., description="Number of healthy files")
    scan_time: float = Field(..., description="Total scan time in seconds")
    success_rate: Optional[float] = Field(None, description="Success rate in percent")
    was_resumed: Optional[bool] = Field(None, description="Whether scan was resumed")
    deep_scans_needed: Optional[int] = Field(None, description="Files requiring deep scan")
    deep_scans_completed: Optional[int] = Field(None, description="Deep scans completed")

    class Config:
        use_enum_values = True
        json_encoders: ClassVar = {
            ScanMode: lambda v: v.value,
        }
