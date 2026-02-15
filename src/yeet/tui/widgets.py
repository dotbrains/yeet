"""Custom widgets for the yeet TUI."""

from __future__ import annotations

from pathlib import Path

from rich.text import Text
from textual.widgets import Static

from yeet.finder import RelatedFile


class FileItem(Static):
    """A widget representing a file item with checkbox."""

    DEFAULT_CSS = """
    FileItem {
        height: 1;
        padding: 0 1;
    }
    FileItem:hover {
        background: $surface-lighten-1;
    }
    FileItem.selected {
        background: $primary-darken-2;
    }
    FileItem .checkbox {
        width: 3;
    }
    FileItem .size {
        text-align: right;
        width: 10;
    }
    FileItem.sudo .path {
        color: $warning;
    }
    """

    def __init__(
        self,
        file: RelatedFile,
        checked: bool = True,
        show_checkbox: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.file = file
        self.checked = checked
        self.show_checkbox = show_checkbox
        if file.requires_sudo:
            self.add_class("sudo")

    def compose_text(self) -> Text:
        """Compose the text representation of this file item."""
        text = Text()

        if self.show_checkbox:
            checkbox = "☑ " if self.checked else "☐ "
            text.append(checkbox, style="bold green" if self.checked else "dim")

        # Path (truncate if needed)
        path_str = str(self.file.path)
        home = str(Path.home())
        if path_str.startswith(home):
            path_str = "~" + path_str[len(home):]

        style = "yellow" if self.file.requires_sudo else ""
        text.append(path_str, style=style)

        # Size (right-aligned)
        size_str = f"  {self.file.size_human}"
        text.append(size_str, style="cyan")

        return text

    def render(self) -> Text:
        """Render the widget."""
        return self.compose_text()

    def toggle(self) -> None:
        """Toggle the checkbox state."""
        self.checked = not self.checked
        self.refresh()
