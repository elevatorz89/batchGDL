from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, Tree

from ..config import single_list_option_labels, subscription_option_labels
from .common import DOWNLOAD_ALL_LABEL, ConfigChanged, reload_config_from_disk
from .controls import Controls


class Sidebar(Widget):
    BORDER_TITLE = "Menu"

    def compose(self) -> ComposeResult:
        yield Tree("Menu", id="download-tree", classes="sidebar-tree")
        yield Button("Refresh", id="sidebar-refresh-button", flat=True, classes="refresh-button")

    def on_mount(self) -> None:
        self.refresh_tree()

    @on(Button.Pressed, "#sidebar-refresh-button")
    def on_refresh_pressed(self, event: Button.Pressed) -> None:
        reload_config_from_disk(self)

    def refresh_tree(self) -> None:
        tree = self.query_one("#download-tree", Tree)
        tree.clear()
        tree.show_root = False
        tree.root.expand()

        download = tree.root.add("Download", data="none", expand=True, allow_expand=False)
        single_tree = download.add("Single", data="none", expand=True)
        for name in single_list_option_labels():
            single_tree.add_leaf(name, data=("single", name))
        subscription_tree = download.add("Subscriptions", data="none", expand=True)
        for name in subscription_option_labels(DOWNLOAD_ALL_LABEL):
            subscription_tree.add_leaf(name, data=("subscription", name))

        tree.root.add("Search", data="search", allow_expand=False)
        tree.root.add("Settings", data="settings", allow_expand=False)
        tree.root.add("------", data="none", allow_expand=False)
        tree.root.add("Add New List", data="add_list", allow_expand=False)


class SidebarTest(Horizontal):

    def __init__(self) -> None:
        super().__init__(classes="sidebar-layout")

    def compose(self) -> ComposeResult:
        yield Sidebar()
        yield Controls()

    @on(Tree.NodeSelected, "#download-tree")
    def on_download_tree_selected(self, event: Tree.NodeSelected) -> None:
        self.query_one(Controls).show_for_selection(event.node.data)

    @on(ConfigChanged)
    def on_config_changed(self, event: ConfigChanged) -> None:
        event.stop()
        self.query_one(Sidebar).refresh_tree()
        self.query_one(Controls).reload_from_config()
