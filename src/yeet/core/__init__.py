"""Core business logic for yeet."""

from yeet.core.cleaner import (
    DeletionResult,
    check_running_process,
    delete_file,
    delete_files,
    quit_application,
)
from yeet.core.finder import find_related_files
from yeet.core.models import FinderResult, RelatedFile, format_size
from yeet.core.scanner import Application, find_application, scan_applications

__all__ = [
    # Models
    "Application",
    "DeletionResult",
    "FinderResult",
    "RelatedFile",
    "format_size",
    # Scanner
    "find_application",
    "scan_applications",
    # Finder
    "find_related_files",
    # Cleaner
    "check_running_process",
    "delete_file",
    "delete_files",
    "quit_application",
]
