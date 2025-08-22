"""
CLI-specific credential handling utilities.

This module provides CLI-specific wrappers around the core credential
validation functionality.
"""

import os
import sys

import click

from src.core.credential_validator import (
    CredentialValidationResult,
    format_credential_error_details,
)


def handle_credential_error(
    validation_result: CredentialValidationResult, verbose: bool = False
) -> None:
    """
    Handle credential validation errors by showing CLI-appropriate messages
    and exiting.

    This is a CLI-specific wrapper around the core credential validation.

    Args:
        validation_result: Result from credential validation
        verbose: Whether to show additional detail
    """
    if validation_result.is_valid:
        # If validation passes, there's nothing to handle
        return

    error_details = format_credential_error_details(validation_result, verbose)

    # Show main error message
    click.echo(f"Error: {error_details['message']}", err=True)

    # Show additional details in verbose mode
    verbose_conditions = error_details["missing_files"] or error_details["empty_files"]
    if verbose and verbose_conditions:
        click.echo("\nDetailed information:", err=True)
        if error_details["missing_files"]:
            missing = ", ".join(error_details["missing_files"])
            click.echo(f"  Missing files: {missing}", err=True)
        if error_details["empty_files"]:
            empty = ", ".join(error_details["empty_files"])
            click.echo(f"  Empty files: {empty}", err=True)

        click.echo("\nTo fix this:", err=True)
        for i, instruction in enumerate(error_details["fix_instructions"], 1):
            click.echo(f"  {i}. {instruction}", err=True)

    # In test environments, raise ValueError for easier testing
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        msg = f"Trakt credentials not configured: {validation_result.error_message}"
        raise ValueError(msg)

    raise click.Abort
