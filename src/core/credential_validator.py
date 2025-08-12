"""
Credential validation utilities for Trakt.tv integration.

Provides early validation of credentials to give clear error messages
instead of cryptic HTTP errors.

This module is interface-agnostic and does not depend on any specific
presentation layer (CLI, web, GUI, etc.).
"""

import logging
import os
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)


class CredentialValidationResult(NamedTuple):
    """Result of credential validation."""

    is_valid: bool
    error_message: str | None
    missing_files: list[str]
    empty_files: list[str]


def validate_trakt_secrets(secrets_dir: Path | None = None) -> CredentialValidationResult:
    """
    Validate Trakt secret files exist and contain content.

    Args:
        secrets_dir: Path to directory containing secret files. If None, uses the TRAKT_SECRETS_DIR environment variable or defaults to 'docker/secrets'.

    Returns:
        CredentialValidationResult with validation status and details
    """
    if secrets_dir is None:
        secrets_dir_str = os.environ.get("TRAKT_SECRETS_DIR", "docker/secrets")
        secrets_dir = Path(secrets_dir_str)
    required_files = ["trakt_client_id.txt", "trakt_client_secret.txt"]
    missing_files = []
    empty_files = []

    for filename in required_files:
        file_path = secrets_dir / filename

        if not file_path.exists():
            missing_files.append(filename)
            continue

        try:
            content = file_path.read_text().strip()
            if not content:
                empty_files.append(filename)
        except Exception as e:
            logger.warning(f"Error reading {filename}: {e}")
            empty_files.append(filename)

    if missing_files or empty_files:
        error_parts = []
        if missing_files:
            error_parts.append(f"Missing files: {', '.join(missing_files)}")
        if empty_files:
            error_parts.append(f"Empty files: {', '.join(empty_files)}")

        error_message = (
            f"Trakt credentials not configured. {' '.join(error_parts)}. "
            f"Run `make secrets-init` then populate trakt_client_id.txt and trakt_client_secret.txt."
        )

        return CredentialValidationResult(
            is_valid=False,
            error_message=error_message,
            missing_files=missing_files,
            empty_files=empty_files,
        )

    return CredentialValidationResult(
        is_valid=True, error_message=None, missing_files=[], empty_files=[]
    )


def validate_trakt_access_token(token: str | None) -> CredentialValidationResult:
    """
    Validate that an access token is provided and not empty.

    Args:
        token: Access token to validate

    Returns:
        CredentialValidationResult with validation status
    """
    if not token or not token.strip():
        error_message = (
            "Trakt access token is required. "
            "Provide it using the --token option. "
            "See docs/trakt.md for instructions on obtaining a token."
        )
        return CredentialValidationResult(
            is_valid=False, error_message=error_message, missing_files=[], empty_files=[]
        )

    return CredentialValidationResult(
        is_valid=True, error_message=None, missing_files=[], empty_files=[]
    )


def format_credential_error_details(
    validation_result: CredentialValidationResult, verbose: bool = False
) -> dict[str, str | list[str]]:
    """
    Format credential validation error details for presentation.

    This function returns structured error information that can be used
    by any presentation layer to display appropriate error messages.

    Args:
        validation_result: Result from credential validation
        verbose: Whether to include additional detail

    Returns:
        Dictionary containing error information:
        - message: Main error message
        - missing_files: List of missing files (if any)
        - empty_files: List of empty files (if any)
        - fix_instructions: List of fix instructions (if verbose)
    """
    if validation_result.is_valid:
        return {"message": "", "missing_files": [], "empty_files": [], "fix_instructions": []}

    details = {
        "message": validation_result.error_message or "Credential validation failed",
        "missing_files": validation_result.missing_files,
        "empty_files": validation_result.empty_files,
        "fix_instructions": [],
    }

    if verbose:
        details["fix_instructions"] = [
            "Run: make secrets-init",
            "Edit docker/secrets/trakt_client_id.txt with your Trakt client ID",
            "Edit docker/secrets/trakt_client_secret.txt with your Trakt client secret",
            "See docs/trakt.md for detailed setup instructions",
        ]

    return details
