
@dataclass(frozen=True)
class VideoFile:
    """Represents a video file with its properties.
    
    Attributes:
        path: Filesystem path to the video file
        size: File size in bytes (computed automatically)
        duration: Video duration in seconds (set by scanner)
    """

    path: Path
    size: int = field(init=False)
    duration: float = 0.0

    def __post_init__(self) -> None:
        """Initialize file size if file exists."""
        if self.path.exists():
            object.__setattr__(self, "size", self.path.stat().st_size)
        else:
            object.__setattr__(self, "size", 0)

    @property
    def filename(self) -> str:
        """Get the filename as string for backward compatibility."""
        return str(self.path)

    @property
    def name(self) -> str:
        """Get just the filename without path."""
        return self.path.name

    @property
    def stem(self) -> str:
        """Get filename without extension."""
        return self.path.stem

    @property
    def suffix(self) -> str:
        """Get file extension."""
        return self.path.suffix

    @property
    def exists(self) -> bool:
        """Check if file exists on filesystem."""
        return self.path.exists()

    def __str__(self) -> str:
        """String representation showing path and size."""
        size_mb = self.size / (1024 * 1024) if self.size else 0
        return f"{self.path} ({size_mb:.1f} MB)"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "path": str(self.path),
            "size": self.size,
            "duration": self.duration,
            "name": self.name,
            "stem": self.stem,
            "suffix": self.suffix,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VideoFile:
        """Create VideoFile from dictionary."""
        video_file = cls(Path(data["path"]))
        if "duration" in data:
            object.__setattr__(video_file, "duration", data["duration"])
        return video_file


@dataclass
class MediaInfo:
    """Parsed media information from filename.
    
    Attributes:
        title: Cleaned media title
        year: Release year if detected
        media_type: Type of media (movie/tv show)
        season: Season number for TV shows
        episode: Episode number for TV shows  
        quality: Video quality (1080p, 4K, etc.)
        source: Source format (BluRay, WEB-DL, etc.)
        codec: Video codec (x264, H.265, etc.)
        original_filename: Original filename before parsing
    """

    title: str
    year: int | None = None
    media_type: MediaType = MediaType.MOVIE
    season: int | None = None
    episode: int | None = None
    quality: str | None = None
    source: str | None = None
    codec: str | None = None
    original_filename: str = ""

    # Class constants for validation
    MIN_YEAR: ClassVar[int] = 1888  # First known motion picture
    MAX_YEAR: ClassVar[int] = 2030  # Reasonable future limit

    def __post_init__(self) -> None:
        """Clean up and validate media info."""
        self.title = self._clean_title(self.title)
        self._validate_year()

    def _clean_title(self, title: str) -> str:
        """Clean up title by removing dots, underscores, etc.
        
        Args:
            title: Raw title string
            
        Returns:
            Cleaned title string
        """
        import re

        # Replace dots and underscores with spaces
        title = re.sub(r"[._]", " ", title)
        # Normalize whitespace
        title = re.sub(r"\s+", " ", title)
        return title.strip()

    def _validate_year(self) -> None:
        """Validate year is within reasonable bounds."""
        if self.year and not (self.MIN_YEAR <= self.year <= self.MAX_YEAR):
            self.year = None

    @property
    def display_name(self) -> str:
        """Get display name with year if available."""
        if self.year:
            return f"{self.title} ({self.year})"
        return self.title

    @property
    def is_tv_show(self) -> bool:
        """Check if this is a TV show."""
        return self.media_type == MediaType.TV_SHOW

    @property
    def is_movie(self) -> bool:
        """Check if this is a movie."""
        return self.media_type == MediaType.MOVIE

    @property
    def season_episode_string(self) -> str | None:
        """Get season/episode string if available (e.g., 'S01E05')."""
        if self.season is not None and self.episode is not None:
            return f"S{self.season:02d}E{self.episode:02d}"
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "year": self.year,
            "media_type": self.media_type.value,
            "season": self.season,
            "episode": self.episode,
            "quality": self.quality,
            "source": self.source,
            "codec": self.codec,
            "original_filename": self.original_filename,
            "display_name": self.display_name,
            "is_tv_show": self.is_tv_show,
            "is_movie": self.is_movie,
            "season_episode_string": self.season_episode_string,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MediaInfo:
        """Create MediaInfo from dictionary."""
        return cls(
            title=data["title"],
            year=data.get("year"),
            media_type=MediaType(data.get("media_type", "movie")),
            season=data.get("season"),
            episode=data.get("episode"),
            quality=data.get("quality"),
            source=data.get("source"),
            codec=data.get("codec"),
            original_filename=data.get("original_filename", ""),
        )




# Data classes for specialized operations




class CorruptVideoInspectorError(Exception):
    """Base exception for all application errors.
    
    This is the root exception that all other application-specific
    exceptions inherit from. It provides a common base for error handling.
    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize the exception.
        
        Args:
            message: Human-readable error message
            cause: Optional underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.cause = cause

    def __str__(self) -> str:
        """Get string representation of the error."""
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "cause": str(self.cause) if self.cause else None,
        }

class MediaType(Enum):
    """Types of media content.
    
    Attributes:
        MOVIE: Single movie file
        TV_SHOW: TV show episode
        UNKNOWN: Unable to determine media type
    """

    MOVIE = "movie"
    TV_SHOW = "show"
    UNKNOWN = "unknown"
