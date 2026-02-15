"""Configuration and constants for yeet."""

from pathlib import Path

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
