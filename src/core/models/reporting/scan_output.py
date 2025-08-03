from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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
    success_rate: float | None = Field(None, description="Success rate in percent")
    was_resumed: bool | None = Field(None, description="Whether scan was resumed")
    deep_scans_needed: int | None = Field(None, description="Files requiring deep scan")
    deep_scans_completed: int | None = Field(None, description="Deep scans completed")

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={ScanMode: lambda v: v.value},
    )
