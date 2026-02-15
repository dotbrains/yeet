"""Main TUI application for yeet."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from yeet.cleaner import check_running_process, delete_files, quit_application
from yeet.finder import FinderResult, RelatedFile, find_related_files, format_size
from yeet.scanner import Application, scan_applications


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


class ConfirmScreen(ModalScreen[bool]):
    """A confirmation dialog."""

    BINDINGS: ClassVar = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }
    ConfirmScreen > Container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    ConfirmScreen Label {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }
    ConfirmScreen .buttons {
        width: 100%;
        height: 3;
        align: center middle;
    }
    ConfirmScreen Button {
        margin: 0 1;
    }
    """

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

    DEFAULT_CSS = """
    ResultScreen {
        align: center middle;
    }
    ResultScreen > Container {
        width: 70;
        height: auto;
        max-height: 80%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    ResultScreen .title {
        width: 100%;
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    ResultScreen .stats {
        margin: 1 0;
    }
    ResultScreen Button {
        width: 100%;
        margin-top: 1;
    }
    """

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


class YeetApp(App):
    """The main yeet TUI application."""

    TITLE = "yeet"
    SUB_TITLE = "Remove macOS apps completely"

    BINDINGS: ClassVar = [
        Binding("q", "quit", "Quit"),
        Binding("/", "focus_search", "Search"),
        Binding("escape", "clear_or_back", "Back"),
        Binding("space", "toggle_file", "Toggle", show=False),
        Binding("a", "select_all", "Select All", show=False),
        Binding("n", "select_none", "Select None", show=False),
        Binding("d", "delete", "Delete"),
        Binding("enter", "select_app", "Select", show=False),
    ]

    DEFAULT_CSS = """
    YeetApp {
        layout: horizontal;
    }
    #app-panel {
        width: 1fr;
        border-right: solid $primary;
    }
    #file-panel {
        width: 2fr;
    }
    .panel-title {
        dock: top;
        width: 100%;
        height: 3;
        padding: 1;
        background: $primary-darken-2;
        text-style: bold;
    }
    #search-box {
        dock: top;
        width: 100%;
        height: 3;
        padding: 0 1;
    }
    #app-list {
        height: 1fr;
    }
    #file-list {
        height: 1fr;
    }
    #file-summary {
        dock: bottom;
        width: 100%;
        height: 3;
        padding: 1;
        background: $surface-darken-1;
    }
    #no-selection {
        width: 100%;
        height: 100%;
        content-align: center middle;
        color: $text-muted;
    }
    .warning {
        color: $warning;
    }
    """

    def __init__(self, app_name: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.initial_app_name = app_name
        self.applications: list[Application] = []
        self.selected_app: Application | None = None
        self.finder_result: FinderResult | None = None
        self.file_items: dict[Path, FileListItem] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="app-panel"):
                yield Static("Applications", classes="panel-title")
                yield Input(placeholder="Search apps...", id="search-box")
                yield ListView(id="app-list")
            with Vertical(id="file-panel"):
                yield Static("Files to Delete", classes="panel-title")
                yield VerticalScroll(
                    Static("← Select an app to see related files", id="no-selection"),
                    id="file-list",
                )
                yield Static("", id="file-summary")
        yield Footer()

    def on_mount(self) -> None:
        """Load applications when the app starts."""
        self.load_applications()

        # If an initial app was specified, select it
        if self.initial_app_name:
            for app in self.applications:
                if app.display_name.lower() == self.initial_app_name.lower():
                    self.select_application(app)
                    break

    def load_applications(self, filter_text: str = "") -> None:
        """Load and display applications."""
        self.applications = scan_applications()

        app_list = self.query_one("#app-list", ListView)
        app_list.clear()

        filter_lower = filter_text.lower()
        for app in self.applications:
            if filter_lower and filter_lower not in app.display_name.lower():
                continue
            app_list.append(AppListItem(app))

    @on(Input.Changed, "#search-box")
    def on_search_changed(self, event: Input.Changed) -> None:
        """Filter apps when search text changes."""
        self.load_applications(event.value)

    @on(ListView.Selected, "#app-list")
    def on_app_selected(self, event: ListView.Selected) -> None:
        """Handle app selection from the list."""
        if isinstance(event.item, AppListItem):
            self.select_application(event.item.application)

    def select_application(self, app: Application) -> None:
        """Select an application and scan for related files."""
        self.selected_app = app

        # Check if app is running
        if check_running_process(app.display_name):
            self.push_screen(
                ConfirmScreen(
                    f"{app.display_name} appears to be running.\n"
                    "Would you like to quit it first?"
                ),
                self.handle_quit_app,
            )
        else:
            self.scan_files()

    def handle_quit_app(self, should_quit: bool) -> None:
        """Handle the response to quit app dialog."""
        if should_quit and self.selected_app:
            quit_application(self.selected_app.display_name)
        self.scan_files()

    def scan_files(self) -> None:
        """Scan for files related to the selected application."""
        if not self.selected_app:
            return

        self.finder_result = find_related_files(self.selected_app)
        self.file_items.clear()

        file_scroll = self.query_one("#file-list", VerticalScroll)

        # Remove the "no selection" message if present
        no_selection = file_scroll.query("#no-selection")
        for widget in no_selection:
            widget.remove()

        # Clear existing file list
        file_list = file_scroll.query("ListView")
        for widget in file_list:
            widget.remove()

        # Create new file list
        list_view = ListView(id="file-items")
        file_scroll.mount(list_view)

        for file in self.finder_result.files:
            item = FileListItem(file, checked=True)
            self.file_items[file.path] = item
            list_view.append(item)

        self.update_summary()

    def update_summary(self) -> None:
        """Update the file summary display."""
        if not self.finder_result:
            return

        selected_count = sum(1 for item in self.file_items.values() if item.checked)
        selected_size = sum(
            item.file.size for item in self.file_items.values() if item.checked
        )

        summary = self.query_one("#file-summary", Static)
        text = Text()
        text.append(f"Selected: {selected_count}/{len(self.file_items)} files  ")
        text.append(f"Size: {format_size(selected_size)}", style="cyan")

        if self.finder_result.has_sudo_files:
            text.append("  ⚠ Some files require admin privileges", style="yellow")

        summary.update(text)

    @on(ListView.Selected, "#file-items")
    def on_file_selected(self, event: ListView.Selected) -> None:
        """Toggle file selection when clicked."""
        if isinstance(event.item, FileListItem):
            event.item.toggle()
            self.update_summary()

    def action_focus_search(self) -> None:
        """Focus the search box."""
        self.query_one("#search-box", Input).focus()

    def action_clear_or_back(self) -> None:
        """Clear search or go back."""
        search = self.query_one("#search-box", Input)
        if search.value:
            search.value = ""
        elif self.selected_app:
            self.selected_app = None
            self.finder_result = None
            file_scroll = self.query_one("#file-list", VerticalScroll)
            file_list = file_scroll.query("ListView")
            for widget in file_list:
                widget.remove()
            file_scroll.mount(
                Static("← Select an app to see related files", id="no-selection")
            )
            self.query_one("#file-summary", Static).update("")

    def action_toggle_file(self) -> None:
        """Toggle the currently focused file."""
        try:
            file_list = self.query_one("#file-items", ListView)
            if file_list.highlighted_child and isinstance(
                file_list.highlighted_child, FileListItem
            ):
                file_list.highlighted_child.toggle()
                self.update_summary()
        except Exception:
            pass

    def action_select_all(self) -> None:
        """Select all files."""
        for item in self.file_items.values():
            if not item.checked:
                item.toggle()
        self.update_summary()

    def action_select_none(self) -> None:
        """Deselect all files."""
        for item in self.file_items.values():
            if item.checked:
                item.toggle()
        self.update_summary()

    def action_select_app(self) -> None:
        """Select the currently highlighted app."""
        try:
            app_list = self.query_one("#app-list", ListView)
            if app_list.highlighted_child and isinstance(
                app_list.highlighted_child, AppListItem
            ):
                self.select_application(app_list.highlighted_child.application)
        except Exception:
            pass

    def action_delete(self) -> None:
        """Delete selected files."""
        if not self.finder_result:
            self.notify("No app selected", severity="warning")
            return

        selected_paths = {
            path for path, item in self.file_items.items() if item.checked
        }
        if not selected_paths:
            self.notify("No files selected", severity="warning")
            return

        selected_size = sum(
            item.file.size for item in self.file_items.values() if item.checked
        )

        self.push_screen(
            ConfirmScreen(
                f"Delete {len(selected_paths)} items ({format_size(selected_size)})?\n"
                "Files will be moved to Trash."
            ),
            self.handle_delete_confirm,
        )

    def handle_delete_confirm(self, confirmed: bool) -> None:
        """Handle deletion confirmation."""
        if not confirmed or not self.finder_result:
            return

        selected_paths = {
            path for path, item in self.file_items.items() if item.checked
        }

        result = delete_files(
            self.finder_result,
            selected_paths=selected_paths,
            permanent=False,
            include_sudo_files=False,
        )

        self.push_screen(
            ResultScreen(
                success=len(result.successful),
                failed=len(result.failed),
                freed=result.total_freed,
            ),
            self.handle_result_closed,
        )

    def handle_result_closed(self, _: None) -> None:
        """Handle result screen closed."""
        # Clear selection and go back to app list
        self.action_clear_or_back()
        self.load_applications()


def run_tui(app_name: str | None = None) -> None:
    """Run the TUI application.

    Args:
        app_name: Optional app name to select initially
    """
    app = YeetApp(app_name=app_name)
    app.run()
