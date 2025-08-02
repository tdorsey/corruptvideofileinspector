import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MediaItem(BaseModel):
    """Represents a parsed media item (movie or TV show)"""

    title: str
    year: Optional[int] = None
    media_type: str = Field(default="movie")
    season: Optional[int] = Field(default=None, ge=1)
    episode: Optional[int] = Field(default=None, ge=1)
    original_filename: str = ""

    @field_validator("title")
    def clean_title(cls, v):
        """Clean up title by removing dots, underscores, and normalizing whitespace."""
        if not v:
            raise ValueError("Title cannot be empty")
        # Clean up title (remove dots, underscores, etc.)
        cleaned = re.sub(r"[._]", " ", v).strip()
        return re.sub(r"\s+", " ", cleaned)  # Normalize whitespace

    @field_validator("media_type")
    def validate_media_type(cls, v):
        """Ensure media_type is valid."""
        if v not in ["movie", "show"]:
            return "movie"  # Default fallback
        return v

    def __str__(self) -> str:
        if self.media_type == "show" and self.season and self.episode:
            return f"{self.title} S{self.season:02d}E{self.episode:02d} ({self.year})"
        return f"{self.title} ({self.year}) [{self.media_type}]"


class TraktItem(BaseModel):
    """Represents an item from Trakt API with identifiers"""

    title: str
    year: Optional[int] = Field(default=None, ge=1800, le=2100)
    media_type: str = Field(default="movie", pattern=r"^(movie|show)$")
    trakt_id: Optional[int] = Field(default=None, ge=1)
    imdb_id: Optional[str] = Field(default=None, pattern=r"^tt\d+$")
    tmdb_id: Optional[int] = Field(default=None, ge=1)
    tvdb_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("title")
    def validate_title(cls, v):
        """Ensure title is not empty."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("imdb_id")
    def validate_imdb_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate imdb_id format if present."""
        if v is not None and not re.match(r"^tt\d+$", v):
            raise ValueError("imdb_id must match the pattern ^tt\\d+$")
        return v

    @classmethod
    def from_movie_response(cls, data: Dict[str, Any]) -> "TraktItem":
        """Create TraktItem from Trakt movie API response"""
        ids = data.get("ids", {})
        return cls(
            title=data.get("title", ""),
            year=data.get("year"),
            media_type="movie",
            trakt_id=ids.get("trakt"),
            imdb_id=ids.get("imdb"),
            tmdb_id=ids.get("tmdb"),
        )

    @classmethod
    def from_show_response(cls, data: Dict[str, Any]) -> "TraktItem":
        """Create TraktItem from Trakt show API response"""
        ids = data.get("ids", {})
        return cls(
            title=data.get("title", ""),
            year=data.get("year"),
            media_type="show",
            trakt_id=ids.get("trakt"),
            imdb_id=ids.get("imdb"),
            tmdb_id=ids.get("tmdb"),
            tvdb_id=ids.get("tvdb"),
        )

    def __str__(self) -> str:
        year_str = f"({self.year})" if self.year else "(no year)"
        return f"{self.title} {year_str} [{self.media_type}]"


class SyncResultItem(BaseModel):
    """Represents the result of syncing a single media item"""

    title: str
    year: Optional[int] = None
    type: str = Field(pattern=r"^(movie|show)$")
    status: str = Field(pattern=r"^(added|failed|not_found|skipped|error)$")
    trakt_id: Optional[int] = Field(default=None, ge=1)
    filename: str = ""
    error: Optional[str] = None

    @field_validator("title")
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class TraktSyncSummary(BaseModel):
    """Summary of Trakt watchlist sync operation"""

    total: int = Field(ge=0, description="Total number of items processed")
    movies_added: int = Field(ge=0, description="Number of movies added")
    shows_added: int = Field(ge=0, description="Number of shows added")
    failed: int = Field(ge=0, description="Number of items that failed")
    results: List[SyncResultItem] = Field(
        default_factory=list, description="Detailed results for each item"
    )

    @property
    def success_count(self) -> int:
        """Total number of successfully added items"""
        return self.movies_added + self.shows_added

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage"""
        if self.total == 0:
            return 0.0
        return (self.success_count / self.total) * 100

    def __str__(self) -> str:
        return (
            f"Trakt Sync Summary: {self.success_count}/{self.total} items added "
            f"({self.success_rate:.1f}% success rate)"
        )
