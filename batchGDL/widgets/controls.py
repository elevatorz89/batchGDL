from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import ContentSwitcher, Markdown

from .add_list_pane import AddListPane
from .common import ConfigChanged
from .download_pane import DownloadPane
from .edit_pane import EditPane
from .search_pane import SearchPane
from .settings_pane import SettingsPane


class Controls(Widget):
    BORDER_TITLE = "Controls"

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="content-download", id="controls-switcher"):
            with Horizontal(id="content-download"):
                yield DownloadPane()
                yield EditPane()
            yield SearchPane()
            yield SettingsPane()
            yield AddListPane()
            with Vertical(id="none"):
                yield Markdown("Choose a list or option from the sidebar.")

    def show_for_selection(self, data) -> None:
        switcher = self.query_one("#controls-switcher", ContentSwitcher)

        match data:
            case "search":
                switcher.current = "content-search"
                self._set_selection(None, None)
            case "settings":
                switcher.current = "content-settings"
                self._set_selection(None, None)
            case (("single" | "subscription") as kind, name):
                switcher.current = "content-download"
                self._set_selection(kind, name)
            case "add_list":
                switcher.current = "content-add-list"
                self._set_selection(None, None)
            case _:
                switcher.current = "none"
                self._set_selection(None, None)

    def _set_selection(self, kind: str | None, name: str | None) -> None:
        edit_pane = self.query_one(EditPane)
        if kind and name:
            edit_pane.load_selection(kind, name)
        else:
            edit_pane.clear_selection()
        self.query_one(DownloadPane).set_selection(kind, name)

    def reload_from_config(self) -> None:
        self.query_one(EditPane).reload_from_config()
        self.query_one(SettingsPane).reload_from_config()

    @on(EditPane.Saved)
    def on_edit_pane_saved(self, event: EditPane.Saved) -> None:
        # The entry may have been renamed; keep the download target in sync.
        self.query_one(DownloadPane).set_selection(event.kind, event.name)
        self.post_message(ConfigChanged())

    @on(EditPane.Deleted)
    def on_edit_pane_deleted(self, event: EditPane.Deleted) -> None:
        self.show_for_selection("none")
        self.post_message(ConfigChanged())
