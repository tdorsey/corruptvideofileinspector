"""
Credential validation utilities for Trakt.tv integration.

Provides early validation of credentials to give clear error messages
instead of cryptic HTTP errors.
"""

import logging
import os
import sys
from pathlib import Path
from typing import NamedTuple

import click

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


def handle_credential_error(
    validation_result: CredentialValidationResult, verbose: bool = False
) -> None:
    """
    Handle credential validation errors by showing user-friendly messages and exiting.

    Args:
        validation_result: Result from credential validation
        verbose: Whether to show additional detail
    """
    if validation_result.is_valid:
        return

    # Show main error message
    click.echo(f"Error: {validation_result.error_message}", err=True)

    # Show additional details in verbose mode
    if verbose and (validation_result.missing_files or validation_result.empty_files):
        click.echo("\nDetailed information:", err=True)
        if validation_result.missing_files:
            click.echo(f"  Missing files: {', '.join(validation_result.missing_files)}", err=True)
        if validation_result.empty_files:
            click.echo(f"  Empty files: {', '.join(validation_result.empty_files)}", err=True)

        click.echo("\nTo fix this:", err=True)
        click.echo("  1. Run: make secrets-init", err=True)
        click.echo(
            "  2. Edit docker/secrets/trakt_client_id.txt with your Trakt client ID", err=True
        )
        click.echo(
            "  3. Edit docker/secrets/trakt_client_secret.txt with your Trakt client secret",
            err=True,
        )
        click.echo("  4. See docs/trakt.md for detailed setup instructions", err=True)

    # In test environments, raise ValueError for easier testing
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        raise ValueError(f"Trakt credentials not configured: {validation_result.error_message}")

    raise click.Abort()
