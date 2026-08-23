"""CLI entry point for yeet."""

from __future__ import annotations

import sys

import click

from yeet.cli.banner import print_banner
from yeet.config import CONFIG_PATHS, THEMES, get_config
from yeet.core import (
    delete_files,
    find_application,
    find_related_files,
    format_size,
    scan_applications,
)


@click.command()
@click.argument("app_name", required=False)
@click.option(
    "--dry-run", "-n",
    is_flag=True,
    help="Show what would be deleted without actually deleting.",
)
@click.option(
    "--delete", "-d",
    is_flag=True,
    help="Delete files without launching the TUI.",
)
@click.option(
    "--yes", "-y",
    is_flag=True,
    help="Skip confirmation prompts.",
)
@click.option(
    "--permanent", "-p",
    is_flag=True,
    help="Permanently delete instead of moving to Trash.",
)
@click.option(
    "--list", "-l", "list_apps",
    is_flag=True,
    help="List all installed applications.",
)
@click.option(
    "--init",
    is_flag=True,
    help="Create a default config file at ~/.config/yeet/config.toml",
)
@click.option(
    "--themes",
    is_flag=True,
    help="List available themes.",
)
@click.version_option()
def main(
    app_name: str | None,
    dry_run: bool,
    delete: bool,
    yes: bool,
    permanent: bool,
    list_apps: bool,
    init: bool,
    themes: bool,
) -> None:
    """🚀 yeet - Remove macOS apps completely.

    Launch the TUI to browse and remove applications, or specify an APP_NAME
    to work with a specific application.

    \b
    Examples:
        yeet                    # Launch TUI
        yeet Slack              # Launch TUI with Slack selected
        yeet Slack --dry-run    # Show Slack's related files
        yeet Slack --delete     # Delete Slack and related files
        yeet --list             # List all installed apps
    """
    # Init config mode
    if init:
        print_banner()
        _init_config()
        return

    # List themes mode
    if themes:
        print_banner()
        config = get_config()
        click.echo("Available themes:\n")
        for name in THEMES:
            marker = " (active)" if name == config.theme else ""
            click.echo(f"  • {name}{marker}")
        click.echo(f"\nConfig file: {CONFIG_PATHS[0]}")
        return

    # List mode
    if list_apps:
        print_banner()
        apps = scan_applications()
        click.echo(f"Found {len(apps)} applications:\n")
        for app in apps:
            version = f" (v{app.version})" if app.version else ""
            bundle = f" [{app.bundle_id}]" if app.bundle_id else ""
            click.echo(f"  {app.display_name}{version}{bundle}")
        return

    # If no app specified and not in CLI mode, launch TUI
    if not app_name and not dry_run and not delete:
        from yeet.tui.app import run_tui
        run_tui()
        return

    # CLI mode requires an app name
    if not app_name:
        click.echo("Error: APP_NAME is required for --dry-run or --delete mode.", err=True)
        sys.exit(1)

    # Find the application
    app = find_application(app_name)
    if not app:
        click.echo(f"Error: Application '{app_name}' not found.", err=True)
        click.echo("\nTip: Use 'yeet --list' to see all installed applications.")
        sys.exit(1)

    # Scan for related files
    print_banner()
    click.echo(f"Scanning for files related to {app.display_name}...")
    result = find_related_files(app)

    if not result.files:
        click.echo("No related files found.")
        return

    # Display files
    click.echo(f"\nFound {len(result.files)} items ({result.total_size_human}):\n")
    for file in result.files:
        icon = "📁" if file.is_dir else "📄"
        sudo = " ⚠️" if file.requires_sudo else ""
        click.echo(f"  {icon} {file.path} ({file.size_human}){sudo}")

    if result.has_sudo_files:
        click.echo("\n⚠️  Some files require admin privileges (marked with ⚠️)")

    # Dry run stops here
    if dry_run:
        click.echo(f"\nTotal: {result.total_size_human}")
        click.echo("\n(Dry run - no files were deleted)")
        return

    # Delete mode
    if delete:
        if not yes:
            click.echo(f"\nThis will move {len(result.files)} items to Trash.")
            if permanent:
                click.echo(click.style("WARNING: --permanent will delete files forever!", fg="red"))
            if not click.confirm("Continue?"):
                click.echo("Aborted.")
                return

        click.echo("\nDeleting...")
        deletion_result = delete_files(
            result,
            permanent=permanent,
            include_sudo_files=False,
        )

        click.echo(f"\n✓ Deleted: {len(deletion_result.successful)} items")
        if deletion_result.failed:
            click.echo(f"✗ Failed: {len(deletion_result.failed)} items")
            for file, error in deletion_result.failed:
                click.echo(f"  - {file.path}: {error}", err=True)
        if deletion_result.skipped:
            click.echo(f"⊘ Skipped: {len(deletion_result.skipped)} items (require sudo)")

        click.echo(f"\n💾 Space freed: {format_size(deletion_result.total_freed)}")
        return

    # Default: launch TUI with the app selected
    from yeet.tui.app import run_tui
    run_tui(app_name=app.display_name)


def _init_config() -> None:
    """Create a default config file."""
    config_path = CONFIG_PATHS[0]  # ~/.config/yeet/config.toml

    if config_path.exists():
        click.echo(f"Config file already exists: {config_path}")
        if not click.confirm("Overwrite?"):
            return

    # Create directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write default config
    default_config = '''# yeet configuration file
# Documentation: https://github.com/smeltery/yeet

[appearance]
# Available themes: default, dracula, nord, catppuccin, gruvbox, light
theme = "default"

# Override specific colors (optional)
# [appearance.colors]
# primary = "#7C3AED"
# accent = "#10B981"

[behavior]
# Ask for confirmation before deleting
confirm_delete = true

# Use permanent delete (skip Trash) by default
default_permanent = false

# Include apps from /System/Applications
include_system_apps = false
'''

    config_path.write_text(default_config)
    click.echo(f"✓ Created config file: {config_path}")
    click.echo("\nEdit this file to customize yeet.")
    click.echo("Use 'yeet --themes' to see available themes.")


if __name__ == "__main__":
    main()
