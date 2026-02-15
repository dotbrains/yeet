"""Tests for yeet.core.models."""

from __future__ import annotations

from pathlib import Path

import pytest

from yeet.core.scanner import Application
from yeet.core.models import (
    DeletionResult,
    FinderResult,
    RelatedFile,
    format_size,
)


class TestFormatSize:
    """Tests for format_size function."""

    def test_bytes(self) -> None:
        assert format_size(0) == "0 B"
        assert format_size(1) == "1 B"
        assert format_size(512) == "512 B"
        assert format_size(1023) == "1023 B"

    def test_kilobytes(self) -> None:
        assert format_size(1024) == "1.0 KB"
        assert format_size(1536) == "1.5 KB"
        assert format_size(10240) == "10.0 KB"

    def test_megabytes(self) -> None:
        assert format_size(1024 * 1024) == "1.0 MB"
        assert format_size(1024 * 1024 * 5) == "5.0 MB"

    def test_gigabytes(self) -> None:
        assert format_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_size(1024 * 1024 * 1024 * 2) == "2.0 GB"

    def test_terabytes(self) -> None:
        assert format_size(1024**4) == "1.0 TB"


class TestApplication:
    """Tests for Application dataclass."""

    def test_creation(self, temp_app_bundle: Path) -> None:
        app = Application(
            name="TestApp",
            path=temp_app_bundle,
            bundle_id="com.test.app",
            version="1.0",
        )
        assert app.name == "TestApp"
        assert app.bundle_id == "com.test.app"
        assert app.version == "1.0"

    def test_display_name(self, temp_app_bundle: Path) -> None:
        app = Application(
            name="Different Name",
            path=temp_app_bundle,
            bundle_id=None,
            version=None,
        )
        # display_name comes from path stem, not name
        assert app.display_name == "TestApp"

    def test_str(self, sample_application: Application) -> None:
        assert str(sample_application) == "TestApp"

    def test_optional_fields(self, temp_app_bundle: Path) -> None:
        app = Application(
            name="App",
            path=temp_app_bundle,
            bundle_id=None,
            version=None,
        )
        assert app.bundle_id is None
        assert app.version is None


class TestRelatedFile:
    """Tests for RelatedFile dataclass."""

    def test_file_size_calculation(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")  # 11 bytes

        rf = RelatedFile(path=test_file, is_dir=False)
        assert rf.size == 11
        assert rf.size_human == "11 B"

    def test_dir_size_calculation(self, tmp_path: Path) -> None:
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()
        (test_dir / "a.txt").write_text("a" * 100)
        (test_dir / "b.txt").write_text("b" * 200)

        rf = RelatedFile(path=test_dir, is_dir=True)
        assert rf.size == 300

    def test_nonexistent_path(self, tmp_path: Path) -> None:
        rf = RelatedFile(path=tmp_path / "nonexistent", is_dir=False)
        assert rf.size == 0

    def test_explicit_size(self, tmp_path: Path) -> None:
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Explicit size overrides calculation
        rf = RelatedFile(path=test_file, size=9999, is_dir=False)
        assert rf.size == 9999

    def test_requires_sudo(self, tmp_path: Path) -> None:
        rf = RelatedFile(path=tmp_path / "file", requires_sudo=True)
        assert rf.requires_sudo is True


class TestFinderResult:
    """Tests for FinderResult dataclass."""

    def test_total_size(self, sample_finder_result: FinderResult) -> None:
        total = sample_finder_result.total_size
        assert total > 0
        assert isinstance(sample_finder_result.total_size_human, str)

    def test_has_sudo_files_false(self, sample_finder_result: FinderResult) -> None:
        assert sample_finder_result.has_sudo_files is False

    def test_has_sudo_files_true(
        self, sample_application: Application, tmp_path: Path
    ) -> None:
        sudo_file = RelatedFile(
            path=tmp_path / "sudo_file",
            requires_sudo=True,
        )
        result = FinderResult(app=sample_application, files=[sudo_file])
        assert result.has_sudo_files is True

    def test_empty_files(self, sample_application: Application) -> None:
        result = FinderResult(app=sample_application, files=[])
        assert result.total_size == 0
        assert result.has_sudo_files is False


class TestDeletionResult:
    """Tests for DeletionResult dataclass."""

    def test_empty_result(self) -> None:
        result = DeletionResult()
        assert result.total_freed == 0
        assert result.all_successful is True

    def test_total_freed(self, sample_related_file: RelatedFile) -> None:
        result = DeletionResult(successful=[sample_related_file])
        assert result.total_freed == sample_related_file.size

    def test_all_successful_with_failures(
        self, sample_related_file: RelatedFile
    ) -> None:
        result = DeletionResult(
            successful=[],
            failed=[(sample_related_file, "error")],
        )
        assert result.all_successful is False

    def test_skipped_does_not_affect_success(
        self, sample_related_file: RelatedFile
    ) -> None:
        result = DeletionResult(
            successful=[],
            failed=[],
            skipped=[sample_related_file],
        )
        assert result.all_successful is True
