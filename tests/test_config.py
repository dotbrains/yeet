"""Tests for yeet.config."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import tempfile

import pytest

from yeet.config.settings import (
    THEMES,
    UserConfig,
    get_config,
    CONFIG_PATHS,
)


class TestThemes:
    """Tests for theme configuration."""

    def test_default_theme_exists(self) -> None:
        assert "default" in THEMES

    def test_all_themes_have_required_colors(self) -> None:
        required_colors = {"primary", "secondary", "background", "surface", "error"}
        for name, theme in THEMES.items():
            for color in required_colors:
                assert color in theme, f"Theme '{name}' missing '{color}'"

    def test_theme_colors_are_valid(self) -> None:
        # All color values should be hex codes
        for name, theme in THEMES.items():
            for key, value in theme.items():
                assert value.startswith("#"), f"Theme '{name}' color '{key}' invalid"
                assert len(value) in (4, 7), f"Theme '{name}' color '{key}' wrong length"


class TestUserConfig:
    """Tests for UserConfig dataclass."""

    def test_default_values(self) -> None:
        config = UserConfig()
        assert config.theme == "default"
        assert config.confirm_delete is True
        assert config.default_permanent is False
        assert config.include_system_apps is False

    def test_custom_values(self) -> None:
        config = UserConfig(
            theme="dracula",
            confirm_delete=False,
            default_permanent=True,
        )
        assert config.theme == "dracula"
        assert config.confirm_delete is False

    def test_get_theme_colors(self) -> None:
        config = UserConfig(theme="dracula")
        colors = config.get_theme_colors()
        assert "primary" in colors
        assert colors == THEMES["dracula"]

    def test_get_theme_colors_with_custom(self) -> None:
        config = UserConfig(
            theme="default",
            custom_colors={"primary": "#FF0000"}
        )
        colors = config.get_theme_colors()
        assert colors["primary"] == "#FF0000"  # Custom overrides


class TestUserConfigLoad:
    """Tests for UserConfig.load method."""

    def test_default_config_when_no_file(self, tmp_path: Path) -> None:
        with patch("yeet.config.settings.CONFIG_PATHS", [tmp_path / "nonexistent.toml"]):
            config = UserConfig.load()
            assert config.theme == "default"

    def test_load_from_toml_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[appearance]
theme = "nord"

[behavior]
confirm_delete = false
default_permanent = true
""")

        with patch("yeet.config.settings.CONFIG_PATHS", [config_file]):
            config = UserConfig.load()
            assert config.theme == "nord"
            assert config.confirm_delete is False
            assert config.default_permanent is True

    def test_invalid_toml_returns_default(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("this is not valid toml {{{")

        with patch("yeet.config.settings.CONFIG_PATHS", [config_file]):
            config = UserConfig.load()
            assert config.theme == "default"

    def test_partial_config(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[appearance]
theme = "gruvbox"
""")

        with patch("yeet.config.settings.CONFIG_PATHS", [config_file]):
            config = UserConfig.load()
            assert config.theme == "gruvbox"
            # Other values should be defaults
            assert config.confirm_delete is True

    def test_first_config_file_wins(self, tmp_path: Path) -> None:
        config1 = tmp_path / "config1.toml"
        config2 = tmp_path / "config2.toml"

        config1.write_text('[appearance]\ntheme = "dracula"')
        config2.write_text('[appearance]\ntheme = "nord"')

        with patch("yeet.config.settings.CONFIG_PATHS", [config1, config2]):
            config = UserConfig.load()
            assert config.theme == "dracula"


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_user_config(self) -> None:
        # Just verify it returns a UserConfig instance
        config = get_config()
        assert isinstance(config, UserConfig)

    def test_caches_config(self) -> None:
        # get_config should return the same instance
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
