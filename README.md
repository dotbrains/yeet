# 🗑️ yeet

![yeet](https://raw.githubusercontent.com/dotbrains/yeet/main/assets/og-image.svg)

[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)](https://github.com/dotbrains/yeet)

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)
![macOS](https://img.shields.io/badge/-macOS-000000?style=flat-square&logo=apple&logoColor=white)
![Textual](https://img.shields.io/badge/-Textual-7C3AED?style=flat-square&logo=python&logoColor=white)
![Click](https://img.shields.io/badge/-Click-4EAA25?style=flat-square&logo=python&logoColor=white)
![Pytest](https://img.shields.io/badge/-Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)

A TUI/CLI tool to completely remove macOS applications and all their related files — like AppCleaner, but in your terminal.

## Features

- **Complete removal**: Finds and removes app bundles, preferences, caches, containers, logs, and more
- **Beautiful TUI**: Interactive terminal interface with keyboard navigation
- **CLI mode**: Script-friendly command-line interface for automation
- **Safe by default**: Moves files to Trash (recoverable) unless `--permanent` is specified
- **Dry run**: Preview what would be deleted before committing

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed information about the project structure, data flow, and module responsibilities.

## Requirements

- macOS
- Python 3.10+

## Installation

```bash
# Using pip
pip install .

# Or with pipx (recommended)
pipx install .

# For development
pip install -e .
```

## Usage

### TUI Mode (Interactive)

![tui](https://raw.githubusercontent.com/dotbrains/yeet/main/assets/tui.png)

Launch the interactive interface:

```bash
yeet
```

- Use `/` to search apps
- Navigate with arrow keys or `j`/`k`
- Press `Enter` to select an app
- Press `Space` to toggle files
- Press `d` to delete selected files
- Press `q` to quit

### CLI Mode

```bash
# List all installed applications
yeet --list

# Show files related to an app (dry run)
yeet Slack --dry-run

# Delete an app and all related files
yeet Slack --delete

# Delete without confirmation
yeet Slack --delete --yes

# Permanently delete (skip Trash)
yeet Slack --delete --permanent
```

## What Gets Removed

yeet searches these locations for files matching the app name or bundle identifier:

**User Library** (`~/Library/`):
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

**System Library** (`/Library/`):
- Application Support
- Caches
- Preferences
- LaunchAgents
- LaunchDaemons
- Logs

## Keyboard Shortcuts (TUI)

| Key | Action |
|-----|--------|
| `/` | Focus search |
| `↑`/`↓` or `j`/`k` | Navigate |
| `Enter` | Select app |
| `Space` | Toggle file |
| `a` | Select all files |
| `n` | Select no files |
| `d` | Delete selected |
| `Escape` | Go back / Clear |
| `q` | Quit |

## Configuration

Create a config file to customize yeet:

```bash
yeet --init
```

This creates `~/.config/yeet/config.toml`:

```toml
[appearance]
# Available themes: default, dracula, nord, catppuccin, gruvbox, light
theme = "dracula"

[behavior]
confirm_delete = true
default_permanent = false
include_system_apps = false
```

See available themes:

```bash
yeet --themes
```

## Safety

- **Trash by default**: Files are moved to Trash and can be recovered
- **Confirmation**: Prompts before deletion (use `--yes` to skip)
- **Running apps**: Warns if the app is running and offers to quit it
- **Sudo files**: System-level files that require admin access are marked and skipped by default

## License

MIT
