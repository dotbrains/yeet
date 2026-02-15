"""Data models for yeet."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yeet.core.scanner import Application


def format_size(size: int) -> str:
    """Format a size in bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            if unit == "B":
                return f"{size} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


@dataclass
class RelatedFile:
    """A file or directory related to an application."""

    path: Path
    size: int = 0
    is_dir: bool = False
    requires_sudo: bool = False

    def __post_init__(self) -> None:
        if self.size == 0 and self.path.exists():
            self.size = self._calculate_size()

    def _calculate_size(self) -> int:
        """Calculate the size of the file or directory."""
        try:
            if self.path.is_file():
                return self.path.stat().st_size
            elif self.path.is_dir():
                total = 0
                for dirpath, _, filenames in os.walk(self.path):
                    for filename in filenames:
                        filepath = Path(dirpath) / filename
                        try:
                            total += filepath.stat().st_size
                        except (OSError, PermissionError):
                            pass
                return total
        except (OSError, PermissionError):
            pass
        return 0

    @property
    def size_human(self) -> str:
        """Return human-readable size."""
        return format_size(self.size)


@dataclass
class FinderResult:
    """Result of scanning for related files."""

    app: "Application"
    files: list[RelatedFile] = field(default_factory=list)

    @property
    def total_size(self) -> int:
        """Total size of all related files."""
        return sum(f.size for f in self.files)

    @property
    def total_size_human(self) -> str:
        """Human-readable total size."""
        return format_size(self.total_size)

    @property
    def has_sudo_files(self) -> bool:
        """Whether any files require sudo to delete."""
        return any(f.requires_sudo for f in self.files)


@dataclass
class DeletionResult:
    """Result of a deletion operation."""

    successful: list[RelatedFile] = field(default_factory=list)
    failed: list[tuple[RelatedFile, str]] = field(default_factory=list)
    skipped: list[RelatedFile] = field(default_factory=list)

    @property
    def total_freed(self) -> int:
        """Total bytes freed by successful deletions."""
        return sum(f.size for f in self.successful)

    @property
    def all_successful(self) -> bool:
        """Whether all deletions were successful."""
        return len(self.failed) == 0
