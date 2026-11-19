from textual import on
from textual.app import ComposeResult
from textual.containers import ItemGrid, Vertical
from textual.widgets import Button, Markdown

from ..modals import ListModal, SubscriptionModal
from .common import ConfigChanged


class AddListPane(Vertical):
    def __init__(self) -> None:
        super().__init__(id="content-add-list")

    def compose(self) -> ComposeResult:
        yield Markdown("Add a new single list or subscription.")
        yield ItemGrid(
            Button("Add Single List", id="sidebar-add-list-button"),
            Button("Add Subscription", id="sidebar-add-subscription-button"),
            classes="list-actions",
            min_column_width=18,
        )

    @on(Button.Pressed, "#sidebar-add-list-button")
    def on_add_list_pressed(self, event: Button.Pressed) -> None:
        self.app.push_screen(ListModal(), lambda result: self._after_add(result, "List added."))

    @on(Button.Pressed, "#sidebar-add-subscription-button")
    def on_add_subscription_pressed(self, event: Button.Pressed) -> None:
        self.app.push_screen(
            SubscriptionModal(), lambda result: self._after_add(result, "Subscription added.")
        )

    def _after_add(self, result: bool | None, message: str) -> None:
        if not result:
            return
        self.post_message(ConfigChanged())
        self.notify(message, severity="information")
