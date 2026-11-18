from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, Label, ListItem, ListView, Markdown

from ..search import search


class SearchPane(Vertical):
    def __init__(self) -> None:
        super().__init__(id="content-search")

    def compose(self) -> ComposeResult:
        yield Markdown("Search through your list files. (ENTER key to search)")
        yield Horizontal(Input(id="search-input", select_on_focus=True, placeholder="Search term…"))
        yield Label("", id="search-status")
        yield ListView(id="search-results")

    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        self.run_search()

    def run_search(self) -> None:
        term = self.query_one("#search-input", Input).value.strip()
        results_view = self.query_one("#search-results", ListView)
        status = self.query_one("#search-status", Label)

        results_view.clear()

        if not term:
            status.update("")
            return
        if len(term) < 2:
            status.update("Minimum search length is 2 characters.")
            return

        hits = search(term)
        if not hits:
            status.update("No results.")
            return

        status.update(f"{len(hits)} result(s) for '{term}'")
        for hit in hits:
            label = f"[bold]{hit['file']}:{hit['line_number']}[/bold]  {hit['line']}"
            results_view.append(ListItem(Label(label)))
