"""Configuration and constants for yeet."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Use tomllib (Python 3.11+) or tomli as fallback
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


# Config file locations (checked in order)
CONFIG_PATHS = [
    Path.home() / ".config" / "yeet" / "config.toml",
    Path.home() / ".yeetrc",
]


# Built-in themes
THEMES: dict[str, dict[str, str]] = {
    "default": {
        "primary": "#7C3AED",      # Purple
        "secondary": "#A78BFA",
        "accent": "#10B981",       # Green
        "warning": "#F59E0B",      # Amber
        "error": "#EF4444",        # Red
        "surface": "#1E1E2E",
        "background": "#11111B",
    },
    "dracula": {
        "primary": "#BD93F9",
        "secondary": "#FF79C6",
        "accent": "#50FA7B",
        "warning": "#F1FA8C",
        "error": "#FF5555",
        "surface": "#282A36",
        "background": "#21222C",
    },
    "nord": {
        "primary": "#88C0D0",
        "secondary": "#81A1C1",
        "accent": "#A3BE8C",
        "warning": "#EBCB8B",
        "error": "#BF616A",
        "surface": "#3B4252",
        "background": "#2E3440",
    },
    "catppuccin": {
        "primary": "#CBA6F7",
        "secondary": "#F5C2E7",
        "accent": "#A6E3A1",
        "warning": "#F9E2AF",
        "error": "#F38BA8",
        "surface": "#313244",
        "background": "#1E1E2E",
    },
    "gruvbox": {
        "primary": "#D79921",
        "secondary": "#B8BB26",
        "accent": "#8EC07C",
        "warning": "#FE8019",
        "error": "#FB4934",
        "surface": "#3C3836",
        "background": "#282828",
    },
    "light": {
        "primary": "#6D28D9",
        "secondary": "#8B5CF6",
        "accent": "#059669",
        "warning": "#D97706",
        "error": "#DC2626",
        "surface": "#F3F4F6",
        "background": "#FFFFFF",
    },
}


@dataclass
class UserConfig:
    """User configuration loaded from dotfile."""

    # Appearance
    theme: str = "default"
    custom_colors: dict[str, str] = field(default_factory=dict)

    # Behavior
    confirm_delete: bool = True
    default_permanent: bool = False
    include_system_apps: bool = False
    scan_system_locations: bool = False

    # Paths
    extra_search_paths: list[str] = field(default_factory=list)

    def get_theme_colors(self) -> dict[str, str]:
        """Get the effective theme colors."""
        base = THEMES.get(self.theme, THEMES["default"]).copy()
        base.update(self.custom_colors)
        return base

    @classmethod
    def load(cls) -> "UserConfig":
        """Load configuration from dotfile."""
        config = cls()

        if tomllib is None:
            return config

        for config_path in CONFIG_PATHS:
            if config_path.exists():
                try:
                    with open(config_path, "rb") as f:
                        data = tomllib.load(f)
                    config = cls._from_dict(data)
                    break
                except Exception:
                    # If config is invalid, use defaults
                    pass

        return config

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "UserConfig":
        """Create config from parsed TOML data."""
        config = cls()

        # Appearance section
        if "appearance" in data:
            appearance = data["appearance"]
            if "theme" in appearance:
                config.theme = appearance["theme"]
            if "colors" in appearance:
                config.custom_colors = appearance["colors"]

        # Behavior section
        if "behavior" in data:
            behavior = data["behavior"]
            if "confirm_delete" in behavior:
                config.confirm_delete = behavior["confirm_delete"]
            if "default_permanent" in behavior:
                config.default_permanent = behavior["default_permanent"]
            if "include_system_apps" in behavior:
                config.include_system_apps = behavior["include_system_apps"]
            if "scan_system_locations" in behavior:
                config.scan_system_locations = behavior["scan_system_locations"]

        # Paths section
        if "paths" in data:
            paths = data["paths"]
            if "extra_search" in paths:
                config.extra_search_paths = paths["extra_search"]

        return config


# Global config instance (lazy loaded)
_config: UserConfig | None = None


def get_config() -> UserConfig:
    """Get the global user configuration."""
    global _config
    if _config is None:
        _config = UserConfig.load()
    return _config


def reload_config() -> UserConfig:
    """Reload configuration from disk."""
    global _config
    _config = UserConfig.load()
    return _config


# Locations to search for related files
# Each tuple: (base_path, pattern, requires_sudo)
# Pattern can use {name}, {bundle_id}, {bundle_id_prefix}

USER_LIBRARY = Path.home() / "Library"
SYSTEM_LIBRARY = Path("/Library")

SEARCH_LOCATIONS: list[tuple[Path, str, bool]] = [
    # User Library locations
    (USER_LIBRARY / "Application Support", "{name}", False),
    (USER_LIBRARY / "Application Support", "{bundle_id}", False),
    (USER_LIBRARY / "Caches", "{name}", False),
    (USER_LIBRARY / "Caches", "{bundle_id}", False),
    (USER_LIBRARY / "Preferences", "{bundle_id}.plist", False),
    (USER_LIBRARY / "Preferences", "{bundle_id_prefix}.*.plist", False),
    (USER_LIBRARY / "Logs", "{name}", False),
    (USER_LIBRARY / "Containers", "{bundle_id}", False),
    (USER_LIBRARY / "Group Containers", "*{bundle_id}*", False),
    (USER_LIBRARY / "Saved Application State", "{bundle_id}.savedState", False),
    (USER_LIBRARY / "LaunchAgents", "*{bundle_id}*.plist", False),
    (USER_LIBRARY / "Cookies", "{bundle_id}.binarycookies", False),
    (USER_LIBRARY / "WebKit", "{name}", False),
    (USER_LIBRARY / "HTTPStorages", "{bundle_id}", False),
    (USER_LIBRARY / "Application Scripts", "{bundle_id}", False),
    # System Library locations (require sudo)
    (SYSTEM_LIBRARY / "Application Support", "{name}", True),
    (SYSTEM_LIBRARY / "Application Support", "{bundle_id}", True),
    (SYSTEM_LIBRARY / "Caches", "{name}", True),
    (SYSTEM_LIBRARY / "Caches", "{bundle_id}", True),
    (SYSTEM_LIBRARY / "LaunchAgents", "*{bundle_id}*.plist", True),
    (SYSTEM_LIBRARY / "LaunchDaemons", "*{bundle_id}*.plist", True),
    (SYSTEM_LIBRARY / "Preferences", "{bundle_id}.plist", True),
    (SYSTEM_LIBRARY / "Logs", "{name}", True),
]
