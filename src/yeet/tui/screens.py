"""Modal screens for yeet TUI."""

from __future__ import annotations

from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from yeet.models import format_size


class ConfirmScreen(ModalScreen[bool]):
    """A confirmation dialog."""

    BINDINGS: ClassVar = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.message)
            with Horizontal(classes="buttons"):
                yield Button("Yes", id="yes", variant="error")
                yield Button("No", id="no", variant="primary")

    @on(Button.Pressed, "#yes")
    def on_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def on_no(self) -> None:
        self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class ResultScreen(ModalScreen[None]):
    """Screen showing deletion results."""

    BINDINGS: ClassVar = [
        Binding("enter", "close", "Close"),
        Binding("escape", "close", "Close"),
    ]

    def __init__(self, success: int, failed: int, freed: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.success = success
        self.failed = failed
        self.freed = freed

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("🎉 Deletion Complete!", classes="title")
            with Vertical(classes="stats"):
                yield Static(f"✓ Successfully deleted: [green]{self.success}[/] items")
                if self.failed > 0:
                    yield Static(f"✗ Failed: [red]{self.failed}[/] items")
                yield Static(f"💾 Space freed: [cyan]{format_size(self.freed)}[/]")
            yield Button("Close", id="close", variant="primary")

    @on(Button.Pressed, "#close")
    def on_close(self) -> None:
        self.dismiss(None)

    def action_close(self) -> None:
        self.dismiss(None)
