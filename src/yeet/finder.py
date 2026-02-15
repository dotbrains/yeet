"""Find files related to a macOS application."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from yeet.scanner import Application


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

    app: Application
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


def format_size(size: int) -> str:
    """Format a size in bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            if unit == "B":
                return f"{size} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


# Locations to search for related files
# Each tuple: (base_path, pattern, requires_sudo)
# Pattern can use {name}, {bundle_id}, {bundle_id_prefix}
SEARCH_LOCATIONS: list[tuple[Path, str, bool]] = [
    # User Library locations
    (Path.home() / "Library" / "Application Support", "{name}", False),
    (Path.home() / "Library" / "Application Support", "{bundle_id}", False),
    (Path.home() / "Library" / "Caches", "{name}", False),
    (Path.home() / "Library" / "Caches", "{bundle_id}", False),
    (Path.home() / "Library" / "Preferences", "{bundle_id}.plist", False),
    (Path.home() / "Library" / "Preferences", "{bundle_id_prefix}.*.plist", False),
    (Path.home() / "Library" / "Logs", "{name}", False),
    (Path.home() / "Library" / "Containers", "{bundle_id}", False),
    (Path.home() / "Library" / "Group Containers", "*{bundle_id}*", False),
    (Path.home() / "Library" / "Saved Application State", "{bundle_id}.savedState", False),
    (Path.home() / "Library" / "LaunchAgents", "*{bundle_id}*.plist", False),
    (Path.home() / "Library" / "Cookies", "{bundle_id}.binarycookies", False),
    (Path.home() / "Library" / "WebKit", "{name}", False),
    (Path.home() / "Library" / "HTTPStorages", "{bundle_id}", False),
    (Path.home() / "Library" / "Application Scripts", "{bundle_id}", False),
    # System Library locations (require sudo)
    (Path("/Library/Application Support"), "{name}", True),
    (Path("/Library/Application Support"), "{bundle_id}", True),
    (Path("/Library/Caches"), "{name}", True),
    (Path("/Library/Caches"), "{bundle_id}", True),
    (Path("/Library/LaunchAgents"), "*{bundle_id}*.plist", True),
    (Path("/Library/LaunchDaemons"), "*{bundle_id}*.plist", True),
    (Path("/Library/Preferences"), "{bundle_id}.plist", True),
    (Path("/Library/Logs"), "{name}", True),
]


def _match_pattern(base_path: Path, pattern: str) -> list[Path]:
    """Find files matching a pattern in a directory.

    Args:
        base_path: Directory to search in
        pattern: Glob pattern to match

    Returns:
        List of matching paths
    """
    if not base_path.exists():
        return []

    try:
        if "*" in pattern:
            # Use glob for wildcard patterns
            return list(base_path.glob(pattern))
        else:
            # Direct path check
            path = base_path / pattern
            return [path] if path.exists() else []
    except (OSError, PermissionError):
        return []


def find_related_files(app: Application) -> FinderResult:
    """Find all files related to an application.

    Args:
        app: The application to find related files for

    Returns:
        FinderResult containing all discovered related files
    """
    result = FinderResult(app=app)
    seen_paths: set[Path] = set()

    # Always include the app bundle itself
    app_file = RelatedFile(path=app.path, is_dir=True)
    result.files.append(app_file)
    seen_paths.add(app.path)

    # Get search terms
    name = app.name
    display_name = app.display_name
    bundle_id = app.bundle_id

    # Get bundle ID prefix (e.g., "com.apple" from "com.apple.Safari")
    bundle_id_prefix = ".".join(bundle_id.split(".")[:2]) if bundle_id else None

    for base_path, pattern_template, requires_sudo in SEARCH_LOCATIONS:
        # Try different substitutions
        patterns_to_try: list[str] = []

        if "{name}" in pattern_template:
            patterns_to_try.append(pattern_template.replace("{name}", name))
            if display_name != name:
                patterns_to_try.append(pattern_template.replace("{name}", display_name))

        if "{bundle_id}" in pattern_template and bundle_id:
            patterns_to_try.append(pattern_template.replace("{bundle_id}", bundle_id))

        if "{bundle_id_prefix}" in pattern_template and bundle_id_prefix:
            patterns_to_try.append(
                pattern_template.replace("{bundle_id_prefix}", bundle_id_prefix)
            )

        for pattern in patterns_to_try:
            matches = _match_pattern(base_path, pattern)
            for path in matches:
                if path not in seen_paths:
                    seen_paths.add(path)
                    related = RelatedFile(
                        path=path,
                        is_dir=path.is_dir(),
                        requires_sudo=requires_sudo,
                    )
                    result.files.append(related)

    # Sort files: app bundle first, then by path
    result.files.sort(key=lambda f: (f.path != app.path, str(f.path).lower()))

    return result
