"""Pytest fixtures for yeet tests."""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest

from yeet.core.scanner import Application
from yeet.core.models import RelatedFile, FinderResult


@pytest.fixture
def temp_app_bundle(tmp_path: Path) -> Path:
    """Create a temporary .app bundle for testing."""
    app_path = tmp_path / "TestApp.app"
    contents_path = app_path / "Contents"
    contents_path.mkdir(parents=True)

    # Create Info.plist
    info_plist = contents_path / "Info.plist"
    info_plist.write_bytes(
        b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>TestApp</string>
    <key>CFBundleIdentifier</key>
    <string>com.test.testapp</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
</dict>
</plist>"""
    )

    # Create a dummy executable
    macos_path = contents_path / "MacOS"
    macos_path.mkdir()
    (macos_path / "TestApp").write_text("#!/bin/bash\necho 'Test'")

    return app_path


@pytest.fixture
def sample_application(temp_app_bundle: Path) -> Application:
    """Create a sample Application instance."""
    return Application(
        name="TestApp",
        path=temp_app_bundle,
        bundle_id="com.test.testapp",
        version="1.0.0",
    )


@pytest.fixture
def sample_related_file(tmp_path: Path) -> RelatedFile:
    """Create a sample RelatedFile instance."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test content " * 100)  # ~1.3KB
    return RelatedFile(path=test_file, is_dir=False)


@pytest.fixture
def sample_related_dir(tmp_path: Path) -> RelatedFile:
    """Create a sample RelatedFile directory."""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2" * 100)
    return RelatedFile(path=test_dir, is_dir=True)


@pytest.fixture
def sample_finder_result(
    sample_application: Application,
    sample_related_file: RelatedFile,
    sample_related_dir: RelatedFile,
) -> FinderResult:
    """Create a sample FinderResult."""
    return FinderResult(
        app=sample_application,
        files=[sample_related_file, sample_related_dir],
    )


@pytest.fixture
def mock_applications_dir(tmp_path: Path) -> Path:
    """Create a mock /Applications directory with test apps."""
    apps_dir = tmp_path / "Applications"
    apps_dir.mkdir()

    # Create a few test apps
    for name, bundle_id, version in [
        ("App1", "com.test.app1", "1.0"),
        ("App2", "com.test.app2", "2.0"),
        ("NoBundle", None, None),  # App without bundle info
    ]:
        app_path = apps_dir / f"{name}.app" / "Contents"
        app_path.mkdir(parents=True)

        if bundle_id:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{name}</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
</dict>
</plist>"""
            (app_path / "Info.plist").write_text(plist_content)

    return apps_dir
