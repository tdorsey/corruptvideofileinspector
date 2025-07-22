"""
Trakt.tv Watchlist API Integration Tool

A Python-based tool for syncing local media collections to Trakt.tv watchlist
by processing video inspection JSON files and using filename parsing.
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class MediaItem:
    """Represents a parsed media item (movie or TV show)"""

    title: str
    year: Optional[int] = None
    media_type: str = "movie"  # "movie" or "show"
    season: Optional[int] = None
    episode: Optional[int] = None
    original_filename: str = ""

    def __post_init__(self) -> None:
        """Validate and clean up media item data"""
        # Clean up title (remove dots, underscores, etc.)
        self.title = re.sub(r"[._]", " ", self.title).strip()
        self.title = re.sub(r"\s+", " ", self.title)  # Normalize whitespace

        # Ensure media_type is valid
        if self.media_type not in ["movie", "show"]:
            self.media_type = "movie"

        logger.debug(f"MediaItem created: {self.title} ({self.year}) - {self.media_type}")


@dataclass
class TraktItem:
    """Represents an item from Trakt API with identifiers"""

    title: str
    year: Optional[int]
    media_type: str
    trakt_id: Optional[int] = None
    imdb_id: Optional[str] = None
    tmdb_id: Optional[int] = None
    tvdb_id: Optional[int] = None

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


class TraktAPI:
    """Trakt.tv API client for watchlist management"""

    BASE_URL = "https://api.trakt.tv"
    API_VERSION = "2"

    def __init__(self, access_token: str, client_id: Optional[str] = None):
        """
        Initialize Trakt API client

        Args:
            access_token: OAuth 2.0 access token for API authentication
            client_id: Optional client ID for API requests
        """
        self.access_token = access_token
        self.client_id = client_id
        self.session = requests.Session()

        # Set up default headers
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "trakt-api-version": self.API_VERSION,
            }
        )

        if client_id:
            self.session.headers["trakt-api-key"] = client_id

        logger.info("TraktAPI client initialized")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Make authenticated request to Trakt API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: JSON data for POST requests
            params: Query parameters

        Returns:
            requests.Response: API response

        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.BASE_URL}{endpoint}"

        logger.debug(f"Making {method} request to {url}")

        try:
            response = self.session.request(
                method=method, url=url, json=data, params=params, timeout=30
            )

            logger.debug(f"Response status: {response.status_code}")

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                if "Retry-After" not in response.headers:
                    logger.warning(
                        f"'Retry-After' header missing. Using fallback timeout of {retry_after} seconds."
                    )
                else:
                    logger.warning(
                        f"Rate limited, waiting {retry_after} seconds as per 'Retry-After' header."
                    )
                time.sleep(retry_after)
                # Retry the request
                return self._make_request(method, endpoint, data, params)

            return response

        except requests.RequestException as e:
            logger.exception(f"Request failed: {e}")
            raise

    def search_movie(
        self, title: str, year: Optional[int] = None, limit: int = 1
    ) -> List[TraktItem]:
        """
        Search for a movie on Trakt

        Args:
            title: Movie title to search for
            year: Optional release year for better matching
            limit: Maximum number of results to return (default 1 for backward compatibility)

        Returns:
            List[TraktItem]: List of matching movie results, empty if none found
        """
        params = {"query": title}
        if year:
            params["year"] = str(year)

        logger.info(f"Searching for movie: {title} ({year})")

        try:
            response = self._make_request("GET", "/search/movie", params=params)

            if response.status_code == 200:
                results = response.json()

                if results:
                    # Convert results to TraktItem objects
                    trakt_items = []
                    for result in results:
                        movie_data = result.get("movie", {})
                        if movie_data:  # Make sure movie data exists
                            trakt_item = TraktItem.from_movie_response(movie_data)

                            # When year is provided, only include exact year matches
                            if year is not None and trakt_item.year != year:
                                logger.debug(
                                    f"Skipping movie with different year: {trakt_item.title} ({trakt_item.year}) != {year}"
                                )
                                continue

                            trakt_items.append(trakt_item)
                            logger.debug(f"Found movie: {trakt_item.title} ({trakt_item.year})")

                            # Stop if we've reached the limit
                            if len(trakt_items) >= limit:
                                break

                    logger.info(f"Found {len(trakt_items)} movie results for: {title}")
                    return trakt_items
                logger.info(f"No movie results found for: {title}")
                return []
            logger.warning(f"Movie search failed with status {response.status_code}")
            return []

        except Exception as e:
            logger.exception(f"Error searching for movie {title}: {e}")
            return []

    def search_show(
        self, title: str, year: Optional[int] = None, limit: int = 1
    ) -> List[TraktItem]:
        """
        Search for a TV show on Trakt

        Args:
            title: Show title to search for
            year: Optional first air year for better matching
            limit: Maximum number of results to return (default 1 for backward compatibility)

        Returns:
            List[TraktItem]: List of matching show results, empty if none found
        """
        params = {"query": title}
        if year:
            params["year"] = str(year)

        logger.info(f"Searching for TV show: {title} ({year})")

        try:
            response = self._make_request("GET", "/search/show", params=params)

            if response.status_code == 200:
                results = response.json()

                if results:
                    # Convert results to TraktItem objects
                    trakt_items = []
                    for result in results:
                        show_data = result.get("show", {})
                        if show_data:  # Make sure show data exists
                            trakt_item = TraktItem.from_show_response(show_data)

                            # When year is provided, only include exact year matches
                            if year is not None and trakt_item.year != year:
                                logger.debug(
                                    f"Skipping show with different year: {trakt_item.title} ({trakt_item.year}) != {year}"
                                )
                                continue

                            trakt_items.append(trakt_item)
                            logger.debug(f"Found show: {trakt_item.title} ({trakt_item.year})")

                            # Stop if we've reached the limit
                            if len(trakt_items) >= limit:
                                break

                    logger.info(f"Found {len(trakt_items)} show results for: {title}")
                    return trakt_items
                logger.info(f"No show results found for: {title}")
                return []
            logger.warning(f"Show search failed with status {response.status_code}")
            return []

        except Exception as e:
            logger.exception(f"Error searching for show {title}: {e}")
            return []

    def add_movie_to_watchlist(self, trakt_item: TraktItem) -> bool:
        """
        Add a movie to user's watchlist

        Args:
            trakt_item: TraktItem representing the movie to add

        Returns:
            bool: True if successfully added, False otherwise
        """
        if trakt_item.media_type != "movie":
            logger.error(f"Item is not a movie: {trakt_item.media_type}")
            return False

        # Prepare movie data for watchlist
        movie_data = {"movies": [{"title": trakt_item.title, "year": trakt_item.year, "ids": {}}]}

        # Add available IDs
        if trakt_item.trakt_id:
            movie_data["movies"][0]["ids"]["trakt"] = trakt_item.trakt_id
        if trakt_item.imdb_id:
            movie_data["movies"][0]["ids"]["imdb"] = trakt_item.imdb_id
        if trakt_item.tmdb_id:
            movie_data["movies"][0]["ids"]["tmdb"] = trakt_item.tmdb_id

        logger.info(f"Adding movie to watchlist: {trakt_item.title}")

        try:
            response = self._make_request("POST", "/sync/watchlist", data=movie_data)

            if response.status_code == 201:
                result = response.json()
                added = result.get("added", {}).get("movies", 0)
                if added > 0:
                    logger.info(f"Successfully added movie to watchlist: {trakt_item.title}")
                    return True
                logger.warning(
                    f"Movie was not added (may already be in watchlist): {trakt_item.title}"
                )
                return True  # Consider this a success
            logger.error(f"Failed to add movie to watchlist: {response.status_code}")
            return False

        except Exception as e:
            logger.exception(f"Error adding movie to watchlist: {e}")
            return False

    def add_show_to_watchlist(self, trakt_item: TraktItem) -> bool:
        """
        Add a TV show to user's watchlist

        Args:
            trakt_item: TraktItem representing the show to add

        Returns:
            bool: True if successfully added, False otherwise
        """
        if trakt_item.media_type != "show":
            logger.error(f"Item is not a show: {trakt_item.media_type}")
            return False

        # Prepare show data for watchlist
        show_data = {"shows": [{"title": trakt_item.title, "year": trakt_item.year, "ids": {}}]}

        # Add available IDs
        if trakt_item.trakt_id:
            show_data["shows"][0]["ids"]["trakt"] = trakt_item.trakt_id
        if trakt_item.imdb_id:
            show_data["shows"][0]["ids"]["imdb"] = trakt_item.imdb_id
        if trakt_item.tmdb_id:
            show_data["shows"][0]["ids"]["tmdb"] = trakt_item.tmdb_id
        if trakt_item.tvdb_id:
            show_data["shows"][0]["ids"]["tvdb"] = trakt_item.tvdb_id

        logger.info(f"Adding show to watchlist: {trakt_item.title}")

        try:
            response = self._make_request("POST", "/sync/watchlist", data=show_data)

            if response.status_code == 201:
                result = response.json()
                added = result.get("added", {}).get("shows", 0)
                if added > 0:
                    logger.info(f"Successfully added show to watchlist: {trakt_item.title}")
                    return True
                logger.warning(
                    f"Show was not added (may already be in watchlist): {trakt_item.title}"
                )
                return True  # Consider this a success
            logger.error(f"Failed to add show to watchlist: {response.status_code}")
            return False

        except Exception as e:
            logger.exception(f"Error adding show to watchlist: {e}")
            return False


def interactive_select_item(items: List[TraktItem], media_item: MediaItem) -> Optional[TraktItem]:
    """
    Interactively select the correct item from search results

    Args:
        items: List of TraktItem search results
        media_item: Original MediaItem being searched for

    Returns:
        TraktItem: Selected item, or None if no selection made
    """
    if not items:
        return None

    if len(items) == 1:
        # Only one result, ask for confirmation
        item = items[0]
        print(f"\nFound 1 match for '{media_item.title}' ({media_item.year}):")
        print(f"  → {item.title} ({item.year}) [{item.media_type}]")

        while True:
            choice = input("Accept this match? [Y/n]: ").strip().lower()
            if choice in ["", "y", "yes"]:
                logger.info(f"User accepted match: {item.title} ({item.year})")
                return item
            if choice in ["n", "no"]:
                logger.info(f"User rejected match for: {media_item.title}")
                return None
            print("Please enter 'y' for yes or 'n' for no.")

    # Multiple results, show selection menu
    print(f"\nFound {len(items)} matches for '{media_item.title}' ({media_item.year}):")
    print("  0. Skip (don't add to watchlist)")

    for i, item in enumerate(items, 1):
        year_str = f"({item.year})" if item.year else "(no year)"
        print(f"  {i}. {item.title} {year_str} [{item.media_type}]")

    while True:
        try:
            choice = input(f"\nSelect an option [0-{len(items)}]: ").strip()

            if not choice:
                continue

            choice_num = int(choice)

            if choice_num == 0:
                logger.info(f"User chose to skip: {media_item.title}")
                return None
            if 1 <= choice_num <= len(items):
                selected_item = items[choice_num - 1]
                logger.info(f"User selected: {selected_item.title} ({selected_item.year})")
                return selected_item
            print(f"Please enter a number between 0 and {len(items)}.")

        except ValueError:
            print(f"Please enter a valid number between 0 and {len(items)}.")
        except KeyboardInterrupt:
            print("\nSelection cancelled.")
            logger.info(f"User cancelled selection for: {media_item.title}")
            return None


class FilenameParser:
    """Parser for extracting media information from filenames"""

    # Patterns for movie filenames
    MOVIE_PATTERNS = [
        # Movie.Name.2023.1080p.BluRay.x264.mkv
        r"^(.+?)\.(\d{4})\.(?:\d+p|BluRay|WEB|HDTV|x264|H264)",
        # Movie Name (2023) [quality].ext
        r"^(.+?)\s*\((\d{4})\)",
        # Movie.Name.2023.mkv (simpler pattern)
        r"^(.+?)\.(\d{4})(?:\.|$)",
        # Movie Name 2023 quality.ext
        r"^(.+?)\s+(\d{4})\s+",
        # Movie.Name.mkv (no year, with file extension)
        r"^(.+?)\.(?:mkv|mp4|avi|mov|wmv|flv|webm|m4v|mpg|mpeg|3gp|asf)$",
        # Final fallback: any filename
        r"^(.+)$",
    ]

    # Patterns for TV show filenames
    TV_PATTERNS = [
        # Show.Name.S01E01.Episode.Title.2023.mkv
        r"^(.+?)\.S(\d+)E(\d+)",
        # Show Name S01E01 Episode Title (2023).mkv
        r"^(.+?)\s+S(\d+)E(\d+)",
        # Show.Name.1x01.Episode.Title.mkv
        r"^(.+?)\.(\d+)x(\d+)",
        # Show Name 1x01 Episode Title.mkv
        r"^(.+?)\s+(\d+)x(\d+)",
    ]

    @classmethod
    def parse_filename(cls, filename: str) -> MediaItem:
        """
        Parse filename to extract media information

        Args:
            filename: Full path or filename to parse

        Returns:
            MediaItem: Parsed media item with title, year, and type
        """
        # Get just the filename without path and extension
        base_name = Path(filename).stem

        logger.debug(f"Parsing filename: {base_name}")

        # First try TV show patterns
        for pattern in cls.TV_PATTERNS:
            match = re.search(pattern, base_name, re.IGNORECASE)
            if match:
                title = match.group(1)
                season = int(match.group(2))
                episode = int(match.group(3))

                # Extract year if present in the remaining part
                year_match = re.search(r"(\d{4})", base_name[match.end() :])
                year = int(year_match.group(1)) if year_match else None

                media_item = MediaItem(
                    title=title,
                    year=year,
                    media_type="show",
                    season=season,
                    episode=episode,
                    original_filename=filename,
                )

                logger.info(f"Parsed as TV show: {media_item.title} S{season:02d}E{episode:02d}")
                return media_item

        # Try movie patterns
        for pattern in cls.MOVIE_PATTERNS:
            match = re.search(pattern, base_name, re.IGNORECASE)
            if match:
                title = match.group(1)
                year = None

                # Check if pattern captured year
                if len(match.groups()) > 1 and match.group(2).isdigit():
                    year = int(match.group(2))
                else:
                    # Look for year in the title
                    year_match = re.search(r"(\d{4})", title)
                    if year_match:
                        year = int(year_match.group(1))
                        title = title.replace(year_match.group(0), "").strip()

                media_item = MediaItem(
                    title=title, year=year, media_type="movie", original_filename=filename
                )

                logger.info(f"Parsed as movie: {media_item.title} ({year})")
                return media_item

        # Fallback: treat as movie with just the filename as title
        media_item = MediaItem(title=base_name, media_type="movie", original_filename=filename)

        logger.warning(f"Could not parse filename, treating as movie: {base_name}")
        return media_item


def process_scan_file(file_path: str) -> List[MediaItem]:
    """
    Process a JSON scan file to extract media items

    Args:
        file_path: Path to JSON file containing scan results

    Returns:
        List[MediaItem]: List of parsed media items from all files

    Raises:
        FileNotFoundError: If scan file doesn't exist
        json.JSONDecodeError: If scan file is not valid JSON
    """
    logger.info(f"Processing scan file: {file_path}")

    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Scan file not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            scan_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.exception(f"Invalid JSON in scan file: {e}")
        raise

    media_items = []

    # Process scan results
    results = scan_data.get("results", [])
    logger.info(f"Found {len(results)} files in scan results")

    for result in results:
        filename = result.get("filename", "")
        if not filename:
            logger.warning("Skipping result with missing filename")
            continue

        # Parse filename regardless of corruption status
        # (as per requirements: process all files)
        try:
            media_item = FilenameParser.parse_filename(filename)
            media_items.append(media_item)
            logger.debug(f"Added media item: {media_item.title}")
        except Exception as e:
            logger.warning(f"Failed to parse filename {filename}: {e}")
            continue

    logger.info(f"Successfully parsed {len(media_items)} media items")
    return media_items


def sync_to_trakt_watchlist(
    scan_file: str,
    access_token: str,
    client_id: Optional[str] = None,
    verbose: bool = False,
    interactive: bool = False,
) -> Dict[str, Any]:
    """
    Main function to sync scan results to Trakt watchlist

    Args:
        scan_file: Path to JSON scan file
        access_token: Trakt API access token
        client_id: Optional Trakt API client ID
        verbose: Enable verbose output
        interactive: Enable interactive selection of search results

    Returns:
        Dict[str, Any]: Summary of sync operation with counts and results
    """
    logger.info("Starting Trakt watchlist sync")

    if verbose:
        print("Starting Trakt watchlist sync...")
        print(f"Processing scan file: {scan_file}")

    # Initialize API client
    try:
        api = TraktAPI(access_token, client_id)
    except Exception:
        logger.exception("Failed to initialize Trakt API")
        raise

    # Process scan file
    try:
        media_items = process_scan_file(scan_file)
    except Exception:
        logger.exception("Failed to process scan file")
        raise

    if not media_items:
        logger.warning("No media items found to sync")
        if verbose:
            print("No media items found to sync")
        return {"total": 0, "movies_added": 0, "shows_added": 0, "failed": 0}

    # Sync to watchlist
    summary = {
        "total": len(media_items),
        "movies_added": 0,
        "shows_added": 0,
        "failed": 0,
        "results": [],
    }

    if verbose:
        print(f"Found {len(media_items)} media items to sync")
        if interactive:
            print("Interactive mode enabled - you will be prompted to select matches")
        print("Searching and adding to watchlist...")

    for i, media_item in enumerate(media_items, 1):
        if verbose:
            progress = f"({i}/{len(media_items)})"
            print(
                f"  {progress} Processing: {media_item.title} ({media_item.year}) [{media_item.media_type}]"
            )

        try:
            # Search for the item
            if interactive:
                # Interactive mode: get multiple results and let user choose
                search_limit = 5  # Get up to 5 results for selection
                if media_item.media_type == "movie":
                    search_results = api.search_movie(
                        media_item.title, media_item.year, limit=search_limit
                    )
                else:
                    search_results = api.search_show(
                        media_item.title, media_item.year, limit=search_limit
                    )

                # Let user select from results
                trakt_item = interactive_select_item(search_results, media_item)
            else:
                # Automatic mode: get first result only (backward compatibility)
                if media_item.media_type == "movie":
                    search_results = api.search_movie(media_item.title, media_item.year, limit=1)
                else:
                    search_results = api.search_show(media_item.title, media_item.year, limit=1)

                trakt_item = search_results[0] if search_results else None

            if not trakt_item:
                logger.warning(f"No Trakt match found for: {media_item.title}")
                if verbose:
                    print("    ❌ Not found on Trakt" if not interactive else "    ❌ Skipped")
                summary["failed"] += 1
                summary["results"].append(
                    {
                        "title": media_item.title,
                        "year": media_item.year,
                        "type": media_item.media_type,
                        "status": "not_found" if not interactive else "skipped",
                        "filename": media_item.original_filename,
                    }
                )
                continue

            # Add to watchlist
            if media_item.media_type == "movie":
                success = api.add_movie_to_watchlist(trakt_item)
            else:
                success = api.add_show_to_watchlist(trakt_item)

            if success:
                if media_item.media_type == "movie":
                    summary["movies_added"] += 1
                else:
                    summary["shows_added"] += 1

                if verbose:
                    print("    ✅ Added to watchlist")

                summary["results"].append(
                    {
                        "title": trakt_item.title,
                        "year": trakt_item.year,
                        "type": trakt_item.media_type,
                        "status": "added",
                        "trakt_id": trakt_item.trakt_id,
                        "filename": media_item.original_filename,
                    }
                )
            else:
                summary["failed"] += 1
                if verbose:
                    print("    ❌ Failed to add")

                summary["results"].append(
                    {
                        "title": trakt_item.title,
                        "year": trakt_item.year,
                        "type": trakt_item.media_type,
                        "status": "failed",
                        "filename": media_item.original_filename,
                    }
                )

        except Exception as e:
            logger.exception(f"Error processing {media_item.title}")
            summary["failed"] += 1
            if verbose:
                print(f"    ❌ Error: {e}")

            summary["results"].append(
                {
                    "title": media_item.title,
                    "year": media_item.year,
                    "type": media_item.media_type,
                    "status": "error",
                    "error": str(e),
                    "filename": media_item.original_filename,
                }
            )

    # Print summary
    if verbose or logger.isEnabledFor(logging.INFO):
        print("\n" + "=" * 50)
        print("TRAKT SYNC SUMMARY")
        print("=" * 50)
        print(f"Total items processed: {summary['total']}")
        print(f"Movies added: {summary['movies_added']}")
        print(f"Shows added: {summary['shows_added']}")
        print(f"Failed/Not found: {summary['failed']}")
        print(
            f"Success rate: {((summary['movies_added'] + summary['shows_added']) / summary['total'] * 100):.1f}%"
        )

    logger.info(
        f"Trakt sync completed: {summary['movies_added']} movies, {summary['shows_added']} shows added"
    )

    return summary
