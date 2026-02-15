"""File deletion logic for yeet."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from send2trash import send2trash

from yeet.models import DeletionResult, FinderResult

# Re-export for backwards compatibility
__all__ = [
    "delete_file",
    "delete_files",
    "check_running_process",
    "quit_application",
    "DeletionResult",
]


def delete_file(path: Path, permanent: bool = False, use_sudo: bool = False) -> tuple[bool, str]:
    """Delete a single file or directory.

    Args:
        path: Path to delete
        permanent: If True, permanently delete. If False, move to Trash.
        use_sudo: If True, use sudo for deletion (only for permanent deletes)

    Returns:
        Tuple of (success, error_message)
    """
    if not path.exists():
        return True, ""  # Already gone, consider it a success

    try:
        if permanent:
            if use_sudo:
                # Use sudo rm for system files
                cmd = ["sudo", "rm", "-rf", str(path)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return False, result.stderr.strip() or "sudo rm failed"
            else:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        else:
            # Move to Trash (safe, recoverable)
            send2trash(str(path))

        return True, ""

    except PermissionError:
        return False, "Permission denied"
    except Exception as e:
        return False, str(e)


def delete_files(
    finder_result: FinderResult,
    selected_paths: set[Path] | None = None,
    permanent: bool = False,
    include_sudo_files: bool = False,
) -> DeletionResult:
    """Delete files from a finder result.

    Args:
        finder_result: The finder result containing files to delete
        selected_paths: Set of paths to delete. If None, delete all.
        permanent: If True, permanently delete. If False, move to Trash.
        include_sudo_files: If True, attempt to delete files requiring sudo.

    Returns:
        DeletionResult with success/failure information
    """
    result = DeletionResult()

    for file in finder_result.files:
        # Check if this file should be deleted
        if selected_paths is not None and file.path not in selected_paths:
            result.skipped.append(file)
            continue

        # Skip sudo files if not requested
        if file.requires_sudo and not include_sudo_files:
            result.skipped.append(file)
            continue

        # Attempt deletion
        success, error = delete_file(
            file.path,
            permanent=permanent,
            use_sudo=file.requires_sudo and permanent,
        )

        if success:
            result.successful.append(file)
        else:
            result.failed.append((file, error))

    return result


def check_running_process(app_name: str) -> bool:
    """Check if an application is currently running.

    Args:
        app_name: Name of the application to check

    Returns:
        True if the app appears to be running
    """
    try:
        result = subprocess.run(
            ["pgrep", "-i", "-f", app_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def quit_application(app_name: str) -> bool:
    """Attempt to quit an application gracefully.

    Args:
        app_name: Name of the application to quit

    Returns:
        True if the quit command was sent successfully
    """
    try:
        # Use osascript to quit the app gracefully
        script = f'tell application "{app_name}" to quit'
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False
