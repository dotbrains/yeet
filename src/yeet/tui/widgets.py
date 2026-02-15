"""Custom widgets for the yeet TUI."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import ListItem, Static

from yeet.models import RelatedFile
from yeet.scanner import Application

__all__ = ["AppListItem", "FileListItem"]


class AppListItem(ListItem):
    """A list item representing an application."""

    def __init__(self, application: Application, **kwargs) -> None:
        super().__init__(**kwargs)
        self.application = application

    def compose(self) -> ComposeResult:
        text = Text()
        text.append(self.application.display_name, style="bold")
        if self.application.version:
            text.append(f"  v{self.application.version}", style="dim")
        yield Static(text)


class FileListItem(ListItem):
    """A list item representing a file to delete."""

    def __init__(self, file: RelatedFile, checked: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.file = file
        self.checked = checked

    def compose(self) -> ComposeResult:
        yield Static(self._render_text())

    def _render_text(self) -> Text:
        text = Text()

        checkbox = "☑ " if self.checked else "☐ "
        text.append(checkbox, style="bold green" if self.checked else "dim")

        # Path (use ~ for home)
        path_str = str(self.file.path)
        home = str(Path.home())
        if path_str.startswith(home):
            path_str = "~" + path_str[len(home):]

        style = "yellow" if self.file.requires_sudo else ""
        text.append(path_str, style=style)
        text.append(f"  {self.file.size_human}", style="cyan")

        return text

    def toggle(self) -> None:
        """Toggle the checked state."""
        self.checked = not self.checked
        self.query_one(Static).update(self._render_text())
