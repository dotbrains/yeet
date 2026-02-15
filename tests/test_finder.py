"""Tests for yeet.core.finder."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from yeet.core.finder import find_related_files
from yeet.core.scanner import Application


class TestFindRelatedFiles:
    """Tests for find_related_files function."""

    def test_find_by_app_name(
        self, sample_application: Application, tmp_path: Path
    ) -> None:
        # Create some test files that match the app name
        library = tmp_path / "Library"
        prefs = library / "Preferences"
        prefs.mkdir(parents=True)
        (prefs / "com.test.testapp.plist").write_text("plist content")

        caches = library / "Caches" / "TestApp"
        caches.mkdir(parents=True)
        (caches / "cache.db").write_text("cache data")

        # Format: (base_path, pattern_template, requires_sudo)
        search_locations = [
            (prefs, "{bundle_id}.plist", False),
            (prefs, "{name}.plist", False),
            (library / "Caches", "{name}", False),
        ]

        with patch("yeet.core.finder.SEARCH_LOCATIONS", search_locations):
            result = find_related_files(sample_application)

        assert result.app == sample_application
        # Should find the pref file, caches dir, and the app bundle
        paths = {f.path for f in result.files}
        assert prefs / "com.test.testapp.plist" in paths
        assert caches in paths

    def test_find_with_no_bundle_id(self, tmp_path: Path) -> None:
        app_path = tmp_path / "SimpleApp.app"
        app_path.mkdir()

        app = Application(
            name="SimpleApp",
            path=app_path,
            bundle_id=None,
            version=None,
        )

        # Create files matching app name only
        library = tmp_path / "Library"
        support = library / "Application Support" / "SimpleApp"
        support.mkdir(parents=True)
        (support / "data.json").write_text("{}")

        search_locations = [
            (library / "Application Support", "{name}", False),
        ]

        with patch("yeet.core.finder.SEARCH_LOCATIONS", search_locations):
            result = find_related_files(app)

        paths = {f.path for f in result.files}
        assert support in paths

    def test_find_returns_app_bundle(self, sample_application: Application) -> None:
        # Even with no search locations, should return the app bundle
        with patch("yeet.core.finder.SEARCH_LOCATIONS", []):
            result = find_related_files(sample_application)

        # Should contain at least the app bundle itself
        assert len(result.files) == 1
        assert result.files[0].path == sample_application.path

    def test_find_with_requires_sudo(
        self, sample_application: Application, tmp_path: Path
    ) -> None:
        # Simulate /Library (system-level) locations
        system_library = tmp_path / "SystemLibrary"
        launch_agents = system_library / "LaunchAgents"
        launch_agents.mkdir(parents=True)
        (launch_agents / "com.test.testapp.plist").write_text("launch agent")

        search_locations = [
            (launch_agents, "{bundle_id}.plist", True),  # requires_sudo=True
        ]

        with patch("yeet.core.finder.SEARCH_LOCATIONS", search_locations):
            result = find_related_files(sample_application)

        # Should find 2 files: app bundle + launch agent
        assert len(result.files) == 2
        # The launch agent file should be marked as requires_sudo
        sudo_files = [f for f in result.files if f.requires_sudo]
        assert len(sudo_files) == 1
        assert sudo_files[0].path == launch_agents / "com.test.testapp.plist"

    def test_directory_size_calculation(
        self, sample_application: Application, tmp_path: Path
    ) -> None:
        library = tmp_path / "Library"
        app_support = library / "Application Support" / "TestApp"
        app_support.mkdir(parents=True)
        (app_support / "file1.txt").write_text("a" * 100)
        (app_support / "file2.txt").write_text("b" * 200)

        search_locations = [
            (library / "Application Support", "{name}", False),
        ]

        with patch("yeet.core.finder.SEARCH_LOCATIONS", search_locations):
            result = find_related_files(sample_application)

        # Should find the app bundle + app_support directory
        assert len(result.files) == 2
        support_file = next(f for f in result.files if f.path == app_support)
        assert support_file.is_dir is True
        assert support_file.size == 300

    def test_wildcard_patterns(
        self, sample_application: Application, tmp_path: Path
    ) -> None:
        library = tmp_path / "Library"
        prefs = library / "Preferences"
        prefs.mkdir(parents=True)

        # Create files with various patterns
        (prefs / "com.test.testapp.plist").write_text("main")
        (prefs / "com.test.testapp.helper.plist").write_text("helper")

        search_locations = [
            (prefs, "{bundle_id}*.plist", False),
        ]

        with patch("yeet.core.finder.SEARCH_LOCATIONS", search_locations):
            result = find_related_files(sample_application)

        # Should find app bundle + both files matching the wildcard
        assert len(result.files) >= 2
