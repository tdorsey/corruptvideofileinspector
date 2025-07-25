# Public API exports
__all__ = ["ReportConfiguration"]
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar


@dataclass
class ReportConfiguration:
    """Configuration for generating scan reports.

    Attributes:
        output_path: Path where report should be saved
        format: Report format (json, csv, html, text)
        include_healthy: Include healthy files in report
        include_metadata: Include file metadata in report
        include_ffmpeg_output: Include raw FFmpeg output
        group_by_directory: Group results by directory
        sort_by: Sort results by this field
        template_path: Custom template file for reports
    """

    output_path: Path
    format: str = "json"
    include_healthy: bool = False
    include_metadata: bool = True
    include_ffmpeg_output: bool = False
    group_by_directory: bool = True
    sort_by: str = "path"
    template_path: Path | None = None

    # Valid formats
    VALID_FORMATS: ClassVar[set[str]] = {"json", "csv", "html", "text", "xml"}
    VALID_SORT_FIELDS: ClassVar[set[str]] = {
        "path",
        "size",
        "corruption",
        "confidence",
        "scan_time",
    }

    def __post_init__(self) -> None:
        """Validate report configuration."""
        if self.format not in self.VALID_FORMATS:
            raise ValueError(
                f"Invalid format: {self.format}. Must be one of " f"{self.VALID_FORMATS}"
            )
        if self.sort_by not in self.VALID_SORT_FIELDS:
            raise ValueError(
                f"Invalid sort field: {self.sort_by}. Must be one of " f"{self.VALID_SORT_FIELDS}"
            )
        if self.template_path and not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "output_path": str(self.output_path),
            "format": self.format,
            "include_healthy": self.include_healthy,
            "include_metadata": self.include_metadata,
            "include_ffmpeg_output": self.include_ffmpeg_output,
            "group_by_directory": self.group_by_directory,
            "sort_by": self.sort_by,
            "template_path": (str(self.template_path) if self.template_path else None),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportConfiguration":
        """Create ReportConfiguration from dictionary."""
        return cls(
            output_path=Path(data["output_path"]),
            format=data.get("format", "json"),
            include_healthy=data.get("include_healthy", False),
            include_metadata=data.get("include_metadata", True),
            include_ffmpeg_output=data.get("include_ffmpeg_output", False),
            group_by_directory=data.get("group_by_directory", True),
            sort_by=data.get("sort_by", "path"),
            template_path=(Path(data["template_path"]) if data.get("template_path") else None),
        )
