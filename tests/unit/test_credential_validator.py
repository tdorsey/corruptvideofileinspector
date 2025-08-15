"""
Unit tests for Trakt credential validation functionality.

Tests missing secrets files, empty files, and valid credentials scenarios.
"""

import tempfile
from pathlib import Path

import pytest

from src.cli.credential_utils import handle_credential_error
from src.core.credential_validator import (
    CredentialValidationResult,
    validate_trakt_access_token,
    validate_trakt_secrets,
)


def assert_error_message_contains(result: CredentialValidationResult, expected: str) -> None:
    """Helper to safely assert error message content."""
    assert result.error_message is not None
    assert expected in result.error_message


pytestmark = pytest.mark.unit


class TestValidateTraktSecrets:
    """Test Trakt secrets file validation."""

    def test_missing_secrets_directory(self):
        """Test validation when secrets directory doesn't exist."""
        non_existent_dir = Path("/non/existent/directory")
        result = validate_trakt_secrets(non_existent_dir)

        assert not result.is_valid
        assert_error_message_contains(
            result, "Missing files: trakt_client_id.txt, trakt_client_secret.txt"
        )
        assert_error_message_contains(result, "make secrets-init")
        assert result.missing_files == ["trakt_client_id.txt", "trakt_client_secret.txt"]
        assert result.empty_files == []

    def test_missing_client_id_file(self):
        """Test validation when only client_id file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_dir = Path(temp_dir)

            # Create only client_secret file
            (secrets_dir / "trakt_client_secret.txt").write_text("test_secret")

            result = validate_trakt_secrets(secrets_dir)

            assert not result.is_valid
            assert_error_message_contains(result, "Missing files: trakt_client_id.txt")
            assert result.missing_files == ["trakt_client_id.txt"]
            assert result.empty_files == []

    def test_missing_client_secret_file(self):
        """Test validation when only client_secret file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_dir = Path(temp_dir)

            # Create only client_id file
            (secrets_dir / "trakt_client_id.txt").write_text("test_client_id")

            result = validate_trakt_secrets(secrets_dir)

            assert not result.is_valid
            assert_error_message_contains(result, "Missing files: trakt_client_secret.txt")
            assert result.missing_files == ["trakt_client_secret.txt"]
            assert result.empty_files == []

    def test_empty_secrets_files(self):
        """Test validation when secret files exist but are empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_dir = Path(temp_dir)

            # Create empty files
            (secrets_dir / "trakt_client_id.txt").write_text("")
            (secrets_dir / "trakt_client_secret.txt").write_text("   ")  # whitespace only

            result = validate_trakt_secrets(secrets_dir)

            assert not result.is_valid
            assert_error_message_contains(
                result, "Empty files: trakt_client_id.txt, trakt_client_secret.txt"
            )
            assert result.missing_files == []
            assert result.empty_files == ["trakt_client_id.txt", "trakt_client_secret.txt"]

    def test_mixed_missing_and_empty_files(self):
        """Test validation with both missing and empty files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_dir = Path(temp_dir)

            # Create empty client_id file, leave client_secret missing
            (secrets_dir / "trakt_client_id.txt").write_text("")

            result = validate_trakt_secrets(secrets_dir)

            assert not result.is_valid
            assert_error_message_contains(result, "Missing files: trakt_client_secret.txt")
            assert_error_message_contains(result, "Empty files: trakt_client_id.txt")
            assert result.missing_files == ["trakt_client_secret.txt"]
            assert result.empty_files == ["trakt_client_id.txt"]

    def test_valid_secrets_files(self):
        """Test validation when secret files exist and contain content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_dir = Path(temp_dir)

            # Create files with content
            (secrets_dir / "trakt_client_id.txt").write_text("test_client_id")
            (secrets_dir / "trakt_client_secret.txt").write_text("test_client_secret")

            result = validate_trakt_secrets(secrets_dir)

            assert result.is_valid
            assert result.error_message is None
            assert result.missing_files == []
            assert result.empty_files == []

    def test_file_read_error(self):
        """Test handling of file permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_dir = Path(temp_dir)

            # Create one valid file
            (secrets_dir / "trakt_client_id.txt").write_text("test_client_id")

            # Create a file and then make it unreadable by changing permissions
            secret_file = secrets_dir / "trakt_client_secret.txt"
            secret_file.write_text("test_secret")

            # Test by creating a directory with the same name (will cause read error)
            secret_file.unlink()  # Remove the file first
            secret_file.mkdir()  # Create a directory with the same name

            try:
                result = validate_trakt_secrets(secrets_dir)

                assert not result.is_valid
                assert_error_message_contains(result, "Empty files: trakt_client_secret.txt")
                assert result.empty_files == ["trakt_client_secret.txt"]
            finally:
                # Clean up the directory we created
                secret_file.rmdir()


class TestValidateTraktAccessToken:
    """Test access token validation."""

    def test_none_token(self):
        """Test validation with None token."""
        result = validate_trakt_access_token(None)

        assert not result.is_valid
        assert_error_message_contains(result, "Trakt access token is required")
        assert_error_message_contains(result, "Provide it using the --token option")

    def test_empty_token(self):
        """Test validation with empty token."""
        result = validate_trakt_access_token("")

        assert not result.is_valid
        assert_error_message_contains(result, "Trakt access token is required")

    def test_whitespace_only_token(self):
        """Test validation with whitespace-only token."""
        result = validate_trakt_access_token("   ")

        assert not result.is_valid
        assert_error_message_contains(result, "Trakt access token is required")

    def test_valid_token(self):
        """Test validation with valid token."""
        result = validate_trakt_access_token("valid_token_12345")

        assert result.is_valid
        assert result.error_message is None
        assert result.missing_files == []
        assert result.empty_files == []


class TestHandleCredentialError:
    """Test credential error handling."""

    def test_handle_valid_credentials(self):
        """Test that valid credentials don't raise errors."""
        valid_result = CredentialValidationResult(
            is_valid=True, error_message=None, missing_files=[], empty_files=[]
        )

        # Should not raise any exception
        handle_credential_error(valid_result)

    def test_handle_invalid_credentials_raises_abort(self):
        """Test that invalid credentials raise ValueError in test environment."""
        invalid_result = CredentialValidationResult(
            is_valid=False,
            error_message="Test error message",
            missing_files=["trakt_client_id.txt"],
            empty_files=["trakt_client_secret.txt"],
        )

        with pytest.raises(ValueError, match="Trakt credentials not configured"):
            handle_credential_error(invalid_result)

    def test_handle_error_with_verbose_output(self):
        """Test error handling with verbose mode shows additional details."""
        invalid_result = CredentialValidationResult(
            is_valid=False,
            error_message="Test error message",
            missing_files=["trakt_client_id.txt"],
            empty_files=["trakt_client_secret.txt"],
        )

        # We can't easily test the click.echo output, but we can ensure it raises ValueError
        with pytest.raises(ValueError, match="Trakt credentials not configured"):
            handle_credential_error(invalid_result, verbose=True)
