"""Find files related to a macOS application."""

from __future__ import annotations

from pathlib import Path

from yeet.config import SEARCH_LOCATIONS
from yeet.core.models import FinderResult, RelatedFile, format_size
from yeet.core.scanner import Application

# Re-export for backwards compatibility
__all__ = ["find_related_files", "FinderResult", "RelatedFile", "format_size"]


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
