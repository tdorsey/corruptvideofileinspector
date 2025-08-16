import logging
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class MediaItem(BaseModel):
    """Represents a parsed media item (movie or TV show)"""

    title: str
    year: int | None = None
    media_type: str = Field(default="movie")
    season: int | None = Field(default=None, ge=1)
    episode: int | None = Field(default=None, ge=1)
    original_filename: str = ""

    @field_validator("title")
    @classmethod
    def clean_title(cls, v):
        """Clean up title by removing dots, underscores, and normalizing whitespace."""
        if not v:
            msg = "Title cannot be empty"
            raise ValueError(msg)
        # Clean up title (remove dots, underscores, etc.)
        cleaned = re.sub(r"[._]", " ", v).strip()
        return re.sub(r"\s+", " ", cleaned)  # Normalize whitespace

    @field_validator("media_type")
    @classmethod
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
    year: int | None = Field(default=None, ge=1800, le=2100)
    media_type: str = Field(default="movie", pattern=r"^(movie|show)$")
    trakt_id: int | None = Field(default=None, ge=1)
    imdb_id: str | None = Field(default=None, pattern=r"^tt\d+$")
    tmdb_id: int | None = Field(default=None, ge=1)
    tvdb_id: int | None = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Ensure title is not empty."""
        if not v or not v.strip():
            msg = "Title cannot be empty"
            raise ValueError(msg)
        return v.strip()

    @field_validator("imdb_id")
    @classmethod
    def validate_imdb_id(cls, v: str | None) -> str | None:
        """Validate imdb_id format if present."""
        if v is not None and not re.match(r"^tt\d+$", v):
            msg = "imdb_id must match the pattern ^tt\\d+$"
            raise ValueError(msg)
        return v

    @classmethod
    def from_movie_response(cls, data: dict[str, Any]) -> "TraktItem":
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
    def from_show_response(cls, data: dict[str, Any]) -> "TraktItem":
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


class WatchlistInfo(BaseModel):
    """Represents information about a Trakt watchlist/custom list"""

    name: str
    slug: str = Field(description="URL-safe slug for the list")
    trakt_id: int | None = Field(default=None, ge=1)
    description: str | None = None
    privacy: str = Field(default="private", pattern=r"^(private|friends|public)$")
    display_numbers: bool = Field(default=True)
    allow_comments: bool = Field(default=True)
    sort_by: str = Field(default="rank")
    sort_how: str = Field(default="asc", pattern=r"^(asc|desc)$")
    created_at: datetime | None = None
    updated_at: datetime | None = None
    item_count: int = Field(default=0, ge=0)
    comment_count: int = Field(default=0, ge=0)
    like_count: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v or not v.strip():
            msg = "Watchlist name cannot be empty"
            raise ValueError(msg)
        return v.strip()

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        if not v or not v.strip():
            msg = "Watchlist slug cannot be empty"
            raise ValueError(msg)
        # Basic slug validation - should be URL-safe
        if not re.match(r"^[a-z0-9\-_]+$", v):
            msg = "Slug must contain only lowercase letters, numbers, hyphens, and underscores"
            raise ValueError(msg)
        return v.strip()

    @classmethod
    def from_trakt_response(cls, data: dict[str, Any]) -> "WatchlistInfo":
        """Create WatchlistInfo from Trakt API response"""
        ids = data.get("ids", {})
        created_at = None
        updated_at = None

        # Parse datetime strings if present
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError as e:
                logger.warning(f"Failed to parse created_at datetime: {data['created_at']!r} ({e})")

        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"])
            except ValueError as e:
                logger.warning(f"Failed to parse updated_at datetime: {data['updated_at']!r} ({e})")

        return cls(
            name=data.get("name", ""),
            slug=data.get("slug", ""),
            trakt_id=ids.get("trakt"),
            description=data.get("description"),
            privacy=data.get("privacy", "private"),
            display_numbers=data.get("display_numbers", True),
            allow_comments=data.get("allow_comments", True),
            sort_by=data.get("sort_by", "rank"),
            sort_how=data.get("sort_how", "asc"),
            created_at=created_at,
            updated_at=updated_at,
            item_count=data.get("item_count", 0),
            comment_count=data.get("comment_count", 0),
            like_count=data.get("like_count", 0),
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.item_count} items)"


class WatchlistItem(BaseModel):
    """Represents an item in a Trakt watchlist"""

    rank: int | None = Field(default=None, ge=1)
    listed_at: datetime | None = None
    notes: str | None = None
    type: str = Field(pattern=r"^(movie|show)$")

    # The actual media item (movie or show data)
    trakt_item: TraktItem

    @classmethod
    def from_trakt_response(cls, data: dict[str, Any]) -> "WatchlistItem":
        """Create WatchlistItem from Trakt API response"""
        listed_at = None
        if data.get("listed_at"):
            try:
                listed_at = datetime.fromisoformat(data["listed_at"])
            except ValueError as e:
                logger.warning(
                    "Failed to parse listed_at datetime from value '%s': %s", data["listed_at"], e
                )

        # Determine type and extract media data
        if "movie" in data:
            media_type = "movie"
            media_data = data["movie"]
            trakt_item = TraktItem.from_movie_response(media_data)
        elif "show" in data:
            media_type = "show"
            media_data = data["show"]
            trakt_item = TraktItem.from_show_response(media_data)
        else:
            msg = "Response must contain either 'movie' or 'show' data"
            raise ValueError(msg)

        return cls(
            rank=data.get("rank"),
            listed_at=listed_at,
            notes=data.get("notes"),
            type=media_type,
            trakt_item=trakt_item,
        )

    def __str__(self) -> str:
        rank_str = f"#{self.rank}: " if self.rank else ""
        return f"{rank_str}{self.trakt_item}"


class SyncResultItem(BaseModel):
    """Represents the result of syncing a single media item"""

    title: str
    year: int | None = None
    type: str = Field(pattern=r"^(movie|show)$")
    status: str = Field(pattern=r"^(added|failed|not_found|skipped|error)$")
    trakt_id: int | None = Field(default=None, ge=1)
    filename: str = ""
    error: str | None = None
    watchlist: str | None = Field(default=None, description="Name or slug of the target watchlist")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty."""
        if not v or not v.strip():
            msg = "Title cannot be empty"
            raise ValueError(msg)
        return v.strip()


class TraktSyncSummary(BaseModel):
    """Summary of Trakt watchlist sync operation"""

    total: int = Field(ge=0, description="Total number of items processed")
    movies_added: int = Field(ge=0, description="Number of movies added")
    shows_added: int = Field(ge=0, description="Number of shows added")
    failed: int = Field(ge=0, description="Number of items that failed")
    watchlist: str | None = Field(default=None, description="Name or slug of the target watchlist")
    results: list[SyncResultItem] = Field(
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
        watchlist_str = f" to '{self.watchlist}'" if self.watchlist else ""
        return (
            f"Trakt Sync Summary{watchlist_str}: {self.success_count}/{self.total} items added "
            f"({self.success_rate:.1f}% success rate)"
        )
