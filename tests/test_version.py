"""Tests for version functionality."""

import re
from unittest.mock import Mock, patch

import pytest

from src.version import __version__, get_version


def test_version_is_string():
    """Test that version is a string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_format():
    """Test that version follows semantic versioning format or development format."""
    # Should match either semantic versioning (x.y.z) or development version (x.y.z+dev)
    semver_pattern = r"^\d+\.\d+\.\d+(?:[-+].*)?$"
    dev_pattern = r"^0\.0\.0\+dev$"
    
    assert re.match(semver_pattern, __version__) or re.match(dev_pattern, __version__)


def test_get_version_function():
    """Test the get_version function."""
    version = get_version()
    assert isinstance(version, str)
    assert len(version) > 0
    assert version == __version__


def test_get_version_fallback():
    """Test that get_version falls back gracefully when package is not found."""
    with patch("src.version.version", side_effect=Exception("Package not found")):
        with patch("src.version.PackageNotFoundError", Exception):
            version = get_version()
            assert version == "0.0.0+dev"


def test_version_consistency():
    """Test that version is consistent across imports."""
    from src.version import __version__ as version1
    from src.version import get_version
    
    version2 = get_version()
    assert version1 == version2