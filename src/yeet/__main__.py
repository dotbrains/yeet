"""CLI entry point for yeet."""

from __future__ import annotations

import sys

import click

from yeet.cleaner import delete_files
from yeet.finder import find_related_files, format_size
from yeet.scanner import find_application, scan_applications


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
@click.version_option()
def main(
    app_name: str | None,
    dry_run: bool,
    delete: bool,
    yes: bool,
    permanent: bool,
    list_apps: bool,
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
    # List mode
    if list_apps:
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


if __name__ == "__main__":
    main()
