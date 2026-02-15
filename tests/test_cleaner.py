"""Tests for yeet.core.cleaner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from yeet.core.cleaner import (
    delete_file,
    delete_files,
    check_running_process,
    quit_application,
)
from yeet.core.scanner import Application
from yeet.core.models import RelatedFile, FinderResult, DeletionResult


class TestDeleteFile:
    """Tests for delete_file function."""

    def test_delete_file_to_trash(self, tmp_path: Path) -> None:
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("delete me")

        with patch("yeet.core.cleaner.send2trash") as mock_trash:
            success, error = delete_file(test_file, permanent=False)

        assert success is True
        assert error == ""
        mock_trash.assert_called_once_with(str(test_file))

    def test_delete_file_permanent(self, tmp_path: Path) -> None:
        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("delete me")

        success, error = delete_file(test_file, permanent=True)

        assert success is True
        assert error == ""
        assert not test_file.exists()

    def test_delete_directory_permanent(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "to_delete"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        success, error = delete_file(test_dir, permanent=True)

        assert success is True
        assert not test_dir.exists()

    def test_delete_nonexistent_file(self, tmp_path: Path) -> None:
        success, error = delete_file(tmp_path / "nonexistent", permanent=True)

        # Should succeed (nothing to delete)
        assert success is True

    def test_delete_file_error(self, tmp_path: Path) -> None:
        test_file = tmp_path / "error_file.txt"
        test_file.write_text("content")

        with patch("yeet.core.cleaner.send2trash", side_effect=Exception("fail")):
            success, error = delete_file(test_file, permanent=False)

        assert success is False
        assert "fail" in error


class TestDeleteFiles:
    """Tests for delete_files function."""

    def test_delete_multiple_files(
        self, sample_application: Application, tmp_path: Path
    ) -> None:
        files = []
        for i in range(3):
            f = tmp_path / f"file{i}.txt"
            f.write_text(f"content {i}")
            files.append(RelatedFile(path=f, is_dir=False))

        finder_result = FinderResult(app=sample_application, files=files)
        result = delete_files(finder_result, permanent=True)

        assert len(result.successful) == 3
        assert len(result.failed) == 0
        assert result.all_successful is True

    def test_delete_with_selected_paths(
        self, sample_application: Application, tmp_path: Path
    ) -> None:
        file1 = tmp_path / "delete_me.txt"
        file2 = tmp_path / "keep_me.txt"
        file1.write_text("delete")
        file2.write_text("keep")

        files = [
            RelatedFile(path=file1, is_dir=False),
            RelatedFile(path=file2, is_dir=False),
        ]
        finder_result = FinderResult(app=sample_application, files=files)

        # Only delete file1
        result = delete_files(
            finder_result, selected_paths={file1}, permanent=True
        )

        assert len(result.successful) == 1
        assert len(result.skipped) == 1
        assert not file1.exists()
        assert file2.exists()

    def test_delete_empty_finder_result(self, sample_application: Application) -> None:
        finder_result = FinderResult(app=sample_application, files=[])
        result = delete_files(finder_result, permanent=True)

        assert result.all_successful is True
        assert len(result.successful) == 0

    def test_skips_sudo_files_by_default(
        self, sample_application: Application, tmp_path: Path
    ) -> None:
        sudo_file = RelatedFile(
            path=tmp_path / "system_file", requires_sudo=True
        )
        finder_result = FinderResult(app=sample_application, files=[sudo_file])

        result = delete_files(finder_result, permanent=True)

        assert len(result.skipped) == 1
        assert len(result.successful) == 0


class TestCheckRunningProcess:
    """Tests for check_running_process function."""

    def test_process_not_running(self) -> None:
        # Use an app name that definitely won't be running
        is_running = check_running_process("NonexistentApp12345XYZ")
        assert is_running is False

    def test_process_check_with_mock(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "12345"  # PID found

        with patch("subprocess.run", return_value=mock_result):
            is_running = check_running_process("TestApp")
            assert is_running is True

    def test_process_not_found_with_mock(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            is_running = check_running_process("TestApp")
            assert is_running is False


class TestQuitApplication:
    """Tests for quit_application function."""

    def test_quit_application_mock(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            success = quit_application("TestApp")
            assert success is True

    def test_quit_application_failure_mock(self) -> None:
        with patch("subprocess.run", side_effect=Exception("failed")):
            success = quit_application("TestApp")
            assert success is False
