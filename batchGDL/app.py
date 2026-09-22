import json
import os
import subprocess
import sys
import urllib.request

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ItemGrid
from textual.widgets import (
    Header, TabbedContent, TabPane, Markdown, Footer,
    Button, Label, Input, OptionList, Static, ListItem, ListView, Switch, Rule
)

from .config import (
    config, reload_config, entry_extra_flags, global_flags_string,
    job_section, oauth_sites, oauth_option_labels, single_list_option_labels,
    subscription_option_labels, BATCHGDL_CONFIG_PATH, config_file_path,
)
from .constants import SINGLE_LISTS_DIR, SUBSCRIPTION_LISTS_DIR, APP_VERSION, GITHUB_REPO
from .downloads import build_command, build_download_all_command, build_download_job_command, log_download_job
from .lists import lists_txt_path, ensure_list_txt, list_file_is_empty
from .modals import ListModal, SubscriptionModal, DeleteEntryModal, ClearTrashModal, GlobalFlagsModal
from .search import search
from .system import open_editor, spawn_new_console, spawn_new_console_series

_APPEND_LIST_NAME = "#append"
_DOWNLOAD_ALL_LABEL = "-Download All-"


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.lstrip("v").split("."))

_LIST_SELECTION = "#list-selection"
_SUBSCRIPTION_SELECTION = "#subscription-selection"
_OAUTH_SITE_LIST = "#oauth-site-list"


class GdlTui(App):

    CSS_PATH = "style.tcss"
    BINDINGS = [Binding(key="q", action="quit", description="Quit the app")]

    def compose(self) -> ComposeResult:
        yield Header()

        with TabbedContent():
            with TabPane("Single"):
                yield Markdown("Choose a list to download content from it.")
                yield OptionList(*single_list_option_labels(), id="list-selection")
                yield ItemGrid(
                    Button("Download", id="download-button", variant="primary"),
                    Button("Edit List", id="edit-list-button"),
                    Button("Edit Global Flags", id="edit-global-flags-single-button"),
                    Button("Add List", id="add-list-button"),
                    Button("Delete List", id="delete-list-button", variant="error"),
                    Button("Refresh", id="refresh-lists-button"),
                    id="list-actions",
                    min_column_width=14,
                )
            with TabPane("Subscriptions"):
                yield Markdown("Choose a subscription to update.")
                yield OptionList(*subscription_option_labels(_DOWNLOAD_ALL_LABEL), id="subscription-selection")
                yield Horizontal(
                    Static("Append Mode: ", id="append-mode-label"),
                    Switch(id="append"),
                    id="subs-horizontal"
                )
                yield ItemGrid(
                    Button("Download", id="download-subscription-button", variant="primary"),
                    Button("Edit List", id="edit-subscription-list-button"),
                    Button("Edit Append List", id="edit-subscription-append-list-button"),
                    Button("Edit Global Flags", id="edit-global-flags-subscriptions-button"),
                    Button("Add List", id="add-subscription-button"),
                    Button("Delete List", id="delete-subscription-button", variant="error"),
                    Button("Refresh", id="refresh-subscriptions-button"),
                    id="subs-actions",
                    min_column_width=16,
                )

            with TabPane("Search"):
                yield Markdown("Search through your list files. (ENTER key to search)")
                yield Horizontal(
                    Input(id="search-input", select_on_focus=True, placeholder="Search term…"))
                yield Label("", id="search-status")
                yield ListView(id="search-results")
            with TabPane("Config"):
                yield Markdown("Config Menu")
                yield ItemGrid(
                    Button("Edit Downloader Config", id="edit-config-button"),
                    Button("Edit Gallery DL Config", id="edit-gdl-config-button"),
                    Button("Open Log File", id="open-log-file-button"),
                    Button("Update Gallery-DL", id="update-gdl-button"),
                    Button("Check for batchGDL update", id="check-updates-button"),
                    Button("Refresh Config", id="refresh-config-button"),
                    Button("Delete Trashed Lists", id="delete-trashed-lists-button", variant="error"),
                    id="config-actions",
                    min_column_width=22,
                )
                yield Rule()
                yield Markdown("Select an OAuth cache to reset.")
                yield OptionList(*oauth_option_labels(), id="oauth-site-list")
                yield ItemGrid(
                    Button("Reset OAuth Cache", id="reset-oauth-cache-button", variant="error"),
                    id="oauth-grid"
                )
        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        self.title = f"batchGDL v{APP_VERSION}"

    def _selected_option_prompt(self, option_list_id: str) -> str | None:
        option = self.query_one(option_list_id, OptionList).highlighted_option
        if option is None:
            return None
        return str(option.prompt).strip()

    def _require_selection(self, option_list_id: str, message: str) -> str | None:
        prompt = self._selected_option_prompt(option_list_id)
        if not prompt:
            self.notify(message, severity="warning")
        return prompt

    def _require_subscription(self, action: str) -> str | None:
        name = self._require_selection(_SUBSCRIPTION_SELECTION, f"Select a subscription to {action}.")
        if not name:
            return None
        if name == _DOWNLOAD_ALL_LABEL:
            self.notify(f"Select a single subscription to {action}.", severity="warning")
            return None
        return name

    def _open_editor_path(self, path: str) -> None:
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            self.notify(f"File not found: {path}", severity="warning")
            return
        try:
            open_editor(path)
        except OSError as e:
            self.notify(f"Could not open file: {e}", severity="error")

    def _refresh_option_list(self, option_list_id: str, labels: list[str]) -> None:
        option_list = self.query_one(option_list_id, OptionList)
        option_list.clear_options()
        if labels:
            option_list.add_options(labels)
            option_list.highlighted = 0

    def _refresh_after_modal(self, result: bool | None, option_list_id: str, labels: list[str], message: str) -> None:
        if result:
            self._refresh_option_list(option_list_id, labels)
            self.notify(message, severity="information")

    def _single_list_entry(self, name: str) -> tuple[str, str, str] | None:
        entry = job_section("single").get(name)
        if not entry or len(entry) < 2:
            return None
        return entry[0], entry[1], entry_extra_flags(entry, 2)

    def _subscription_entry(self, name: str) -> tuple[str, str, str | None, str] | None:
        entry = job_section("subscription").get(name)
        if not entry or len(entry) < 2:
            return None
        archive = entry[2] if len(entry) > 2 else None
        return entry[0], entry[1], archive, entry_extra_flags(entry, 3)

    def _subscription_list_file(self, name: str) -> str | None:
        entry = self._subscription_entry(name)
        return entry[1] if entry else None

    def _delete_modal(
        self,
        title: str,
        name: str,
        section: str,
        list_file: str | None,
        *,
        lists_dir: str = SUBSCRIPTION_LISTS_DIR,
    ) -> DeleteEntryModal:
        return DeleteEntryModal(
            title,
            name,
            section,
            note=f"The list file will be moved to the list trash folder.",
            list_file=list_file,
            trash_list_file=True,
            lists_dir=lists_dir,
        )

    def _require_nonempty_list(
        self,
        list_file: str,
        *,
        lists_dir: str,
        label: str,
    ) -> bool:
        if list_file_is_empty(list_file, lists_dir):
            self.notify(f"{label} is empty. There's nothing to download.", severity="warning")
            return False
        return True

    def ensure_append_list(self) -> None:
        ensure_list_txt(_APPEND_LIST_NAME, SUBSCRIPTION_LISTS_DIR)

    def refresh_config_ui(self) -> None:
        self._refresh_option_list(_LIST_SELECTION, single_list_option_labels())
        self._refresh_option_list(_SUBSCRIPTION_SELECTION, subscription_option_labels(_DOWNLOAD_ALL_LABEL))
        self._refresh_option_list(_OAUTH_SITE_LIST, oauth_option_labels())

    def refresh_app(self, source_button: Button | None = None) -> None:
        if not os.path.isfile(BATCHGDL_CONFIG_PATH):
            self.notify(f"File not found: {BATCHGDL_CONFIG_PATH}", severity="warning")
            return
        try:
            reload_config()
        except json.JSONDecodeError as e:
            self.notify(f"Invalid config JSON: {e}", severity="error")
            return
        except (OSError, KeyError) as e:
            self.notify(f"Failed to load config: {e}", severity="error")
            return

        if source_button is not None:
            source_button.disabled = True
        try:
            self.refresh_config_ui()
        finally:
            if source_button is not None:
                source_button.disabled = False
        self.notify("Config reloaded.", severity="information")

    def open_lists_txt(self, name: str, lists_dir: str = SUBSCRIPTION_LISTS_DIR) -> None:
        self._open_editor_path(lists_txt_path(name, lists_dir))

    def run_download(
        self,
        *,
        dest_folder: str,
        input_file: str,
        path_key: str,
        archive: str | None = None,
        lists_dir: str = SUBSCRIPTION_LISTS_DIR,
        global_flags: str | None = None,
        extra_flags: str | None = None,
        job_name: str | None = None,
        notify_message: str | None = None,
    ) -> None:
        if job_name:
            try:
                log_download_job(job_name)
            except OSError as e:
                self.notify(f"Could not write log header: {e}", severity="warning")
        if notify_message:
            self.notify(notify_message)
        spawn_new_console(
            build_download_job_command(
                build_command(
                    dest_folder=dest_folder,
                    input_file=input_file,
                    path_key=path_key,
                    archive=archive,
                    lists_dir=lists_dir,
                    global_flags=global_flags,
                    extra_flags=extra_flags,
                ),
                work_dir=os.getcwd(),
            )
        )

    ############################ List ############################

    @on(Button.Pressed, "#add-list-button")
    def on_add_list_pressed(self, event: Button.Pressed) -> None:
        self.push_screen(
            ListModal(),
            lambda result: self._refresh_after_modal(
                result, _LIST_SELECTION, single_list_option_labels(), "List added."
            ),
        )

    @on(Button.Pressed, "#delete-list-button")
    def on_delete_list_pressed(self, event: Button.Pressed) -> None:
        name = self._require_selection(_LIST_SELECTION, "Select a list to delete.")
        if not name:
            return
        entry = self._single_list_entry(name)
        self.push_screen(
            self._delete_modal(
                "Delete List",
                name,
                "single",
                entry[0] if entry else None,
                lists_dir=SINGLE_LISTS_DIR,
            ),
            lambda result: self._refresh_after_modal(
                result, _LIST_SELECTION, single_list_option_labels(), "List removed and file sent to trash."
            ),
        )

    @on(Button.Pressed, "#edit-list-button")
    def on_edit_list_pressed(self, event: Button.Pressed) -> None:
        name = self._require_selection(_LIST_SELECTION, "Select a list to edit.")
        if not name:
            return
        if not self._single_list_entry(name):
            self.notify(f"No list configured for: {name}", severity="warning")
            return
        self.push_screen(
            ListModal(original_name=name),
            lambda result: self._refresh_after_modal(
                result, _LIST_SELECTION, single_list_option_labels(), "List updated."
            ),
        )

    @on(Button.Pressed, "#edit-global-flags-single-button")
    def on_edit_global_flags_single_pressed(self, event: Button.Pressed) -> None:
        self.push_screen(
            GlobalFlagsModal("global-flags-single", "Edit Global Flags (Single)"),
            lambda result: self.notify("Global flags updated.", severity="information") if result else None,
        )

    @on(Button.Pressed, "#download-button")
    def on_download_pressed(self, event: Button.Pressed) -> None:
        name = self._require_selection(_LIST_SELECTION, "Select a list first.")
        if not name:
            return
        entry = self._single_list_entry(name)
        if not entry:
            self.notify(f"No list configured for: {name}", severity="warning")
            return
        list_file, dest_folder, extra_flags = entry
        if not self._require_nonempty_list(list_file, lists_dir=SINGLE_LISTS_DIR, label=f'List "{name}"'):
            return
        self.run_download(
            dest_folder=dest_folder,
            input_file=list_file,
            path_key="list",
            lists_dir=SINGLE_LISTS_DIR,
            global_flags=global_flags_string("global-flags-single"),
            extra_flags=extra_flags,
            job_name=name,
            notify_message=f"Starting download for {name} in a new terminal window.",
        )

    ############################ Subscription ############################

    @on(Button.Pressed, "#add-subscription-button")
    def on_add_subscription_pressed(self, event: Button.Pressed) -> None:
        self.push_screen(
            SubscriptionModal(),
            lambda result: self._refresh_after_modal(
                result, _SUBSCRIPTION_SELECTION, subscription_option_labels(_DOWNLOAD_ALL_LABEL), "Subscription added."
            ),
        )

    @on(Button.Pressed, "#delete-subscription-button")
    def on_delete_subscription_pressed(self, event: Button.Pressed) -> None:
        name = self._require_subscription("delete")
        if not name:
            return
        self.push_screen(
            self._delete_modal("Delete Subscription", name, "subscription", self._subscription_list_file(name)),
            lambda result: self._refresh_after_modal(
                result,
                _SUBSCRIPTION_SELECTION,
                subscription_option_labels(_DOWNLOAD_ALL_LABEL),
                "Subscription removed and file sent to trash.",
            ),
        )

    @on(Button.Pressed, "#edit-subscription-list-button")
    def on_edit_subscription_list_pressed(self, event: Button.Pressed) -> None:
        name = self._require_subscription("edit")
        if not name:
            return
        if not self._subscription_entry(name):
            self.notify(f"No subscription configured for: {name}", severity="warning")
            return
        self.push_screen(
            SubscriptionModal(original_name=name),
            lambda result: self._refresh_after_modal(
                result, _SUBSCRIPTION_SELECTION, subscription_option_labels(_DOWNLOAD_ALL_LABEL), "Subscription updated."
            ),
        )

    @on(Button.Pressed, "#edit-subscription-append-list-button")
    def on_edit_subscription_append_list_pressed(self, event: Button.Pressed) -> None:
        self.ensure_append_list()
        self.open_lists_txt(_APPEND_LIST_NAME)

    @on(Button.Pressed, "#edit-global-flags-subscriptions-button")
    def on_edit_global_flags_subscriptions_pressed(self, event: Button.Pressed) -> None:
        self.push_screen(
            GlobalFlagsModal("global-flags-subscriptions", "Edit Global Flags (Subscriptions)"),
            lambda result: self.notify("Global flags updated.", severity="information") if result else None,
        )

    @on(Switch.Changed, "#append")
    def on_append_mode_changed(self, event: Switch.Changed) -> None:
        if event.value:
            self.ensure_append_list()

    @on(Button.Pressed, "#download-subscription-button")
    def on_download_subscription_pressed(self, event: Button.Pressed) -> None:
        name = self._require_selection(_SUBSCRIPTION_SELECTION, "Select a subscription first.")
        if not name:
            return
        append = self.query_one("#append", Switch).value

        if name == _DOWNLOAD_ALL_LABEL:
            if append:
                self.notify("Turn off Append mode first.", severity="warning")
                return
            subs = job_section("subscription")
            if not subs:
                self.notify("No subscriptions in config.", severity="warning")
                return
            nonempty = {
                sub_name: tup
                for sub_name, tup in subs.items()
                if len(tup) >= 3 and not list_file_is_empty(tup[1], SUBSCRIPTION_LISTS_DIR)
            }
            if not nonempty:
                self.notify("All subscription lists are empty - nothing to download.", severity="warning")
                return
            skipped = len(subs) - len(nonempty)
            if skipped:
                self.notify(
                    f"Skipping {skipped} empty subscription list(s).",
                    severity="warning",
                )
            self.notify("Downloading from all lists in a new terminal…", severity="information")
            spawn_new_console(build_download_all_command(nonempty, work_dir=os.getcwd()), cwd=os.getcwd())
            return

        subscription = self._subscription_entry(name)
        if not subscription:
            self.notify("Unknown subscription.", severity="warning")
            return

        dest_folder, list_file, archive, extra_flags = subscription
        if append:
            self.ensure_append_list()
            input_file = _APPEND_LIST_NAME
            label = "Append list"
            job_name = f"{name} (append)"
        else:
            input_file = list_file
            label = f'Subscription "{name}"'
            job_name = name

        if not self._require_nonempty_list(input_file, lists_dir=SUBSCRIPTION_LISTS_DIR, label=label):
            return

        self.run_download(
            dest_folder=dest_folder,
            input_file=input_file,
            path_key="sub",
            archive=archive,
            global_flags=global_flags_string("global-flags-subscriptions"),
            extra_flags=extra_flags,
            job_name=job_name,
            notify_message=f"Starting download for {name}.",
        )

    ############################ Search ############################

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

    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, event: Input.Submitted) -> None:
        self.run_search()

    ############################ Config ############################

    @on(Button.Pressed, "#refresh-lists-button")
    @on(Button.Pressed, "#refresh-subscriptions-button")
    @on(Button.Pressed, "#refresh-config-button")
    def on_refresh_app_pressed(self, event: Button.Pressed) -> None:
        self.refresh_app(event.button)

    @on(Button.Pressed, "#edit-config-button")
    def on_edit_config_pressed(self, event: Button.Pressed) -> None:
        self._open_editor_path(BATCHGDL_CONFIG_PATH)

    @on(Button.Pressed, "#edit-gdl-config-button")
    def on_edit_gdl_config_pressed(self, event: Button.Pressed) -> None:
        self._open_editor_path(config_file_path())

    @on(Button.Pressed, "#open-log-file-button")
    def on_open_log_file_pressed(self, event: Button.Pressed) -> None:
        self._open_editor_path(config["log_file"])

    @on(Button.Pressed, "#delete-trashed-lists-button")
    def on_delete_trashed_lists_pressed(self, event: Button.Pressed) -> None:
        self.push_screen(ClearTrashModal())

    @on(Button.Pressed, "#update-gdl-button")
    def on_update_gdl_pressed(self, event: Button.Pressed) -> None:
        self.notify("Updating gallery-dl...")
        try:
            spawn_new_console(
                [sys.executable, "-m", "pip", "install", "--break-system-packages", "--upgrade", "gallery-dl"]
            )
        except Exception as e:
            self.notify(f"Error opening updater: {e}", severity="error")

    
    @on(Button.Pressed, "#check-updates-button")
    def on_check_updates_pressed(self, event: Button.Pressed) -> None:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "batchGDL"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                release = json.load(resp)
        except Exception as e:
            self.notify(f"Could not check for updates: {e}", severity="error")
            return
        latest = str(release.get("tag_name", "")).lstrip("v")
        html_url = release.get("html_url") or f"https://github.com/{GITHUB_REPO}/releases/latest"
        try:
            outdated = version_tuple(APP_VERSION) < version_tuple(latest)
        except ValueError:
            self.notify(f"Could not compare versions ({APP_VERSION} vs {latest}).", severity="error")
            return
        if outdated:
            self.notify(
                f'v{latest} is available. [link="{html_url}"]Open release page[/link]',
                severity="warning",
                timeout=10,
            )
            return
        self.notify(f"You're on the latest version ({APP_VERSION}).")

    def selected_oauth_sites(self) -> list[str]:
        prompt = self._selected_option_prompt(_OAUTH_SITE_LIST)
        if prompt is None:
            return []
        if prompt == "All Sites":
            return oauth_sites()
        return [prompt]

    @on(Button.Pressed, "#reset-oauth-cache-button")
    def on_reset_oauth_cache_pressed(self, event: Button.Pressed) -> None:
        sites = self.selected_oauth_sites()
        if not sites:
            self.notify("Nothing configured or selected.", severity="warning")
            return

        gdl_config = config_file_path()
        total = len(sites)
        for idx, site in enumerate(sites, start=1):
            clear = subprocess.run(
                ["gallery-dl", "--clear-cache", site, "--config", gdl_config],
                capture_output=True,
                text=True,
            )
            if clear.returncode != 0:
                err = (clear.stderr or clear.stdout or "").strip()
                self.notify(
                    f"Cache clear for {site} returned {clear.returncode}. {err}",
                    severity="warning",
                )
            if total > 1:
                self.notify(
                    f"OAuth for {site} ({idx} of {total}) - finish this console before the next opens.",
                    severity="information",
                )
            spawn_new_console_series(["gallery-dl", f"oauth:{site}", "--config", gdl_config])

        if total > 1:
            self.notify("Reauth finished.", severity="information")
        else:
            self.notify("Cache Reset; reauth finished (or window was closed).", severity="information")
