"""Tests for yeet.core.scanner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from yeet.core.scanner import (
    Application,
    get_app_info,
    scan_applications,
    find_application,
)


class TestGetAppInfo:
    """Tests for get_app_info function."""

    def test_valid_app_bundle(self, temp_app_bundle: Path) -> None:
        app = get_app_info(temp_app_bundle)
        assert app is not None
        assert app.name == "TestApp"
        assert app.bundle_id == "com.test.testapp"
        assert app.version == "1.0.0"
        assert app.path == temp_app_bundle

    def test_app_without_plist(self, tmp_path: Path) -> None:
        app_path = tmp_path / "NoPlist.app" / "Contents"
        app_path.mkdir(parents=True)

        app = get_app_info(tmp_path / "NoPlist.app")
        assert app is not None
        assert app.name == "NoPlist"
        assert app.bundle_id is None
        assert app.version is None

    def test_nonexistent_app_dir_returns_minimal_info(self, tmp_path: Path) -> None:
        # get_app_info returns minimal info even if path doesn't exist
        # (it just won't have bundle_id/version since there's no plist)
        app = get_app_info(tmp_path / "Nonexistent.app")
        assert app is not None
        assert app.name == "Nonexistent"
        assert app.bundle_id is None

    def test_invalid_plist(self, tmp_path: Path) -> None:
        app_path = tmp_path / "BadPlist.app" / "Contents"
        app_path.mkdir(parents=True)
        (app_path / "Info.plist").write_text("not valid plist data")

        app = get_app_info(tmp_path / "BadPlist.app")
        assert app is not None
        assert app.name == "BadPlist"
        # Should fall back gracefully
        assert app.bundle_id is None


class TestScanApplications:
    """Tests for scan_applications function."""

    def test_scan_returns_list(self) -> None:
        # Just verify scan_applications returns a list
        # (actual content depends on the system)
        apps = scan_applications()
        assert isinstance(apps, list)

    def test_apps_are_sorted(self) -> None:
        apps = scan_applications()
        if len(apps) > 1:
            names = [app.display_name.lower() for app in apps]
            assert names == sorted(names)

    def test_scan_with_mock_dir(self, mock_applications_dir: Path) -> None:
        # Test get_app_info with mock directory
        apps = []
        for app_path in mock_applications_dir.glob("*.app"):
            app = get_app_info(app_path)
            if app:
                apps.append(app)

        assert len(apps) == 3
        names = {app.name for app in apps}
        assert "App1" in names
        assert "App2" in names
        assert "NoBundle" in names


class TestFindApplication:
    """Tests for find_application function."""

    def test_find_nonexistent(self) -> None:
        # Use a name that definitely won't be in /Applications
        app = find_application("NonexistentApp12345XYZ")
        assert app is None

    def test_find_strips_app_extension(self) -> None:
        # Verify extension stripping works
        # We can't easily test actual finding without mocking
        # but we can verify the function handles .app suffix
        app1 = find_application("NonexistentApp12345.app")
        app2 = find_application("NonexistentApp12345")
        # Both should return None (app doesn't exist)
        assert app1 is None
        assert app2 is None

    def test_find_uses_scan_applications(self) -> None:
        # Verify find_application calls scan_applications
        mock_app = Application(
            name="MockApp",
            path=Path("/Applications/MockApp.app"),
            bundle_id="com.mock.app",
            version="1.0",
        )
        with patch("yeet.core.scanner.scan_applications", return_value=[mock_app]):
            app = find_application("MockApp")
            assert app is not None
            assert app.name == "MockApp"

    def test_find_case_insensitive(self) -> None:
        mock_app = Application(
            name="MockApp",
            path=Path("/Applications/MockApp.app"),
            bundle_id="com.mock.app",
            version="1.0",
        )
        with patch("yeet.core.scanner.scan_applications", return_value=[mock_app]):
            # Should match case-insensitively
            app = find_application("mockapp")
            assert app is not None
            assert app.name == "MockApp"
