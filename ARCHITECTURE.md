# Architecture

This document describes the architecture of **yeet**, a macOS application cleaner.

## Overview

yeet is a Python application with two interfaces:
- **CLI** - Command-line interface for scripting and quick operations
- **TUI** - Terminal User Interface for interactive use

```mermaid
flowchart TB
    subgraph Interfaces
        CLI[CLI - Click]
        TUI[TUI - Textual]
    end
    
    subgraph Core["Core Business Logic"]
        Scanner[Scanner]
        Finder[Finder]
        Cleaner[Cleaner]
    end
    
    subgraph Config["Configuration"]
        Settings[User Settings]
        Locations[Search Locations]
    end
    
    subgraph External["External"]
        FS[File System]
        Trash[Trash - send2trash]
        Apps[Applications]
    end
    
    CLI --> Core
    TUI --> Core
    Core --> Config
    Scanner --> Apps
    Finder --> FS
    Cleaner --> Trash
    Cleaner --> FS
```

## Directory Structure

```
src/yeet/
├── __init__.py          # Package version
├── __main__.py          # Entry point
├── cli/                 # Command-line interface
│   ├── __init__.py
│   └── banner.py        # ASCII art banner
├── config/              # Configuration
│   ├── __init__.py      # Re-exports
│   ├── settings.py      # User config, themes
│   └── locations.py     # Search paths
├── core/                # Business logic
│   ├── __init__.py      # Re-exports
│   ├── models.py        # Data classes
│   ├── scanner.py       # App discovery
│   ├── finder.py        # Related file finder
│   └── cleaner.py       # File deletion
└── tui/                 # Terminal UI
    ├── __init__.py
    ├── app.py           # Main Textual app
    ├── screens.py       # Modal dialogs
    ├── widgets.py       # Custom widgets
    └── styles.tcss      # CSS styles
```

## Module Responsibilities

### Core Layer

```mermaid
classDiagram
    class Application {
        +name: str
        +path: Path
        +bundle_id: str
        +version: str
        +display_name: str
    }
    
    class RelatedFile {
        +path: Path
        +size: int
        +is_dir: bool
        +requires_sudo: bool
        +size_human: str
    }
    
    class FinderResult {
        +app: Application
        +files: list[RelatedFile]
        +total_size: int
        +has_sudo_files: bool
    }
    
    class DeletionResult {
        +successful: list[RelatedFile]
        +failed: list[tuple]
        +skipped: list[RelatedFile]
        +total_freed: int
    }
    
    FinderResult --> Application
    FinderResult --> RelatedFile
    DeletionResult --> RelatedFile
```

| Module | Responsibility |
|--------|---------------|
| `models.py` | Data classes: `Application`, `RelatedFile`, `FinderResult`, `DeletionResult` |
| `scanner.py` | Discover installed apps from `/Applications`, extract bundle info from `Info.plist` |
| `finder.py` | Search Library directories for files matching app name or bundle ID |
| `cleaner.py` | Delete files (move to Trash or permanent), quit running apps |

### Config Layer

| Module | Responsibility |
|--------|---------------|
| `settings.py` | Load user config from `~/.config/yeet/config.toml`, theme definitions |
| `locations.py` | Define search paths in `~/Library` and `/Library` |

### CLI Layer

| Module | Responsibility |
|--------|---------------|
| `banner.py` | Generate random ASCII art banners using pyfiglet |
| `__main__.py` | Click command definitions, argument parsing |

### TUI Layer

| Module | Responsibility |
|--------|---------------|
| `app.py` | Main Textual application, keyboard bindings, state management |
| `screens.py` | Modal screens: `ConfirmScreen`, `ResultScreen` |
| `widgets.py` | List item widgets: `AppListItem`, `FileListItem` |
| `styles.tcss` | Textual CSS for layout and theming |

## Data Flow

### App Discovery Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI/TUI
    participant Scanner
    participant FileSystem
    
    User->>CLI/TUI: Launch yeet
    CLI/TUI->>Scanner: scan_applications()
    Scanner->>FileSystem: List /Applications/*.app
    loop Each .app bundle
        Scanner->>FileSystem: Read Info.plist
        FileSystem-->>Scanner: Bundle ID, version, name
    end
    Scanner-->>CLI/TUI: list[Application]
    CLI/TUI-->>User: Display app list
```

### File Finding Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI/TUI
    participant Finder
    participant Config
    participant FileSystem
    
    User->>CLI/TUI: Select app
    CLI/TUI->>Finder: find_related_files(app)
    Finder->>Config: Get SEARCH_LOCATIONS
    Config-->>Finder: List of (path, pattern, sudo)
    loop Each search location
        Finder->>FileSystem: Glob for {name} or {bundle_id}
        FileSystem-->>Finder: Matching paths
    end
    Finder-->>CLI/TUI: FinderResult
    CLI/TUI-->>User: Display file list
```

### Deletion Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI/TUI
    participant Cleaner
    participant Trash
    participant FileSystem
    
    User->>CLI/TUI: Confirm delete
    CLI/TUI->>Cleaner: delete_files(result, paths)
    loop Each selected file
        alt Move to Trash
            Cleaner->>Trash: send2trash(path)
        else Permanent delete
            Cleaner->>FileSystem: rm -rf path
        end
    end
    Cleaner-->>CLI/TUI: DeletionResult
    CLI/TUI-->>User: Show summary
```

## Configuration

### Config File Locations

Checked in order:
1. `~/.config/yeet/config.toml`
2. `~/.yeetrc`

### Config Schema

```toml
[appearance]
theme = "default"  # default, dracula, nord, catppuccin, gruvbox, light

[appearance.colors]  # Optional overrides
primary = "#7C3AED"

[behavior]
confirm_delete = true
default_permanent = false
include_system_apps = false
scan_system_locations = false
```

## Search Locations

yeet searches these directories for app-related files:

### User Library (`~/Library/`)
- Application Support
- Caches
- Preferences (`.plist` files)
- Logs
- Containers
- Group Containers
- Saved Application State
- LaunchAgents
- Cookies
- WebKit
- HTTPStorages
- Application Scripts

### System Library (`/Library/`) - requires sudo
- Application Support
- Caches
- Preferences
- LaunchAgents
- LaunchDaemons
- Logs

## Dependencies

```mermaid
flowchart LR
    subgraph Runtime
        textual[textual - TUI framework]
        click[click - CLI framework]
        send2trash[send2trash - Safe deletion]
        pyfiglet[pyfiglet - ASCII art]
    end
    
    subgraph Stdlib
        plistlib[plistlib - Read Info.plist]
        pathlib[pathlib - Path operations]
        tomllib[tomllib - Config parsing]
    end
    
    yeet --> Runtime
    yeet --> Stdlib
```

## Error Handling

- **Permission errors**: Files requiring sudo are marked and skipped by default
- **Running apps**: User is prompted to quit before deletion
- **Invalid config**: Falls back to defaults silently
- **Missing files**: Treated as successful (already deleted)

## Extension Points

### Adding Search Locations
Edit `config/locations.py` to add new patterns:
```python
SEARCH_LOCATIONS.append(
    (Path.home() / "Library" / "NewLocation", "{bundle_id}", False)
)
```

### Adding Themes
Edit `config/settings.py` to add to `THEMES` dict:
```python
THEMES["mytheme"] = {
    "primary": "#...",
    # ...
}
```

### Adding CLI Commands
Extend `__main__.py` with new Click options or create subcommands.
