"""Database package for scan results persistence."""

from .models import ScanDatabaseModel, ScanResultDatabaseModel
from .service import DatabaseService

__all__ = ["DatabaseService", "ScanDatabaseModel", "ScanResultDatabaseModel"]
