from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from .constants import APP_VERSION
from .widgets import SidebarTest


class GdlTui(App):

    CSS_PATH = "style.tcss"
    BINDINGS = [Binding(key="q", action="quit", description="Quit the app")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield SidebarTest()
        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        self.title = f"batchGDL v{APP_VERSION}"
