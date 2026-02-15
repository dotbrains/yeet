"""Application scanner for discovering installed macOS applications."""

from __future__ import annotations

import plistlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Application:
    """Represents an installed macOS application."""

    name: str
    path: Path
    bundle_id: str | None
    version: str | None

    @property
    def display_name(self) -> str:
        """Return the display name (without .app extension)."""
        return self.path.stem

    def __str__(self) -> str:
        return self.display_name


def get_app_info(app_path: Path) -> Application | None:
    """Extract application info from an .app bundle.

    Args:
        app_path: Path to the .app bundle

    Returns:
        Application instance or None if info couldn't be extracted
    """
    info_plist = app_path / "Contents" / "Info.plist"

    if not info_plist.exists():
        # Some apps might not have Info.plist, create minimal info
        return Application(
            name=app_path.stem,
            path=app_path,
            bundle_id=None,
            version=None,
        )

    try:
        with open(info_plist, "rb") as f:
            plist = plistlib.load(f)

        return Application(
            name=plist.get("CFBundleName", app_path.stem),
            path=app_path,
            bundle_id=plist.get("CFBundleIdentifier"),
            version=plist.get("CFBundleShortVersionString"),
        )
    except Exception:
        # If we can't read the plist, return minimal info
        return Application(
            name=app_path.stem,
            path=app_path,
            bundle_id=None,
            version=None,
        )


def scan_applications(
    include_system: bool = False,
) -> list[Application]:
    """Scan for installed applications.

    Args:
        include_system: Whether to include /System/Applications

    Returns:
        List of discovered applications, sorted by name
    """
    app_dirs = [
        Path("/Applications"),
        Path.home() / "Applications",
    ]

    if include_system:
        app_dirs.append(Path("/System/Applications"))

    applications: list[Application] = []

    for app_dir in app_dirs:
        if not app_dir.exists():
            continue

        # Find all .app bundles (non-recursive, top-level only)
        for app_path in app_dir.glob("*.app"):
            if not app_path.is_dir():
                continue

            app_info = get_app_info(app_path)
            if app_info:
                applications.append(app_info)

    # Sort by display name (case-insensitive)
    applications.sort(key=lambda a: a.display_name.lower())

    return applications


def find_application(name: str) -> Application | None:
    """Find an application by name.

    Args:
        name: Application name (with or without .app extension)

    Returns:
        Application instance or None if not found
    """
    # Normalize the name
    search_name = name.removesuffix(".app").lower()

    for app in scan_applications():
        if app.display_name.lower() == search_name:
            return app
        if app.name.lower() == search_name:
            return app

    return None
