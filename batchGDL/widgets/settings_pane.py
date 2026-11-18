import json
import sys
import urllib.request

from textual import on
from textual.app import ComposeResult
from textual.containers import ItemGrid, Vertical
from textual.widgets import Button, Markdown, OptionList, TabbedContent, TabPane

from ..config import BATCHGDL_CONFIG_PATH, config, config_file_path, oauth_option_labels, oauth_sites
from ..constants import APP_VERSION, GITHUB_REPO
from ..downloads import build_oauth_reset_command
from ..modals import ClearTrashModal
from ..system import spawn_new_console
from .common import open_editor_path, reload_config_from_disk

_OAUTH_ALL_SITES = "All Sites"


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.lstrip("v").split("."))


class SettingsPane(Vertical):
    def __init__(self) -> None:
        super().__init__(id="content-settings")

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Config"):
                yield ItemGrid(
                    Button("Edit batchGDL Config", id="edit-config-button"),
                    Button("Edit Gallery DL Config", id="edit-gdl-config-button"),
                    Button("Open Log File", id="open-log-file-button"),
                    Button("Refresh Config", id="refresh-config-button"),
                    Button("Delete Trashed Lists", id="delete-trashed-lists-button", variant="error"),
                    classes="config-actions",
                    min_column_width=22,
                )
            with TabPane("Update"):
                yield ItemGrid(
                    Button("Update Gallery-DL", id="update-gdl-button"),
                    Button("Check for batchGDL update", id="check-updates-button"),
                    Button("Refresh Config", id="update-refresh-config-button"),
                    classes="config-actions",
                    min_column_width=22,
                )
            with TabPane("OAuth"):
                yield Markdown("Select an OAuth cache to reset.")
                yield OptionList(*oauth_option_labels(), id="oauth-site-list", classes="oauth-site-list")
                yield ItemGrid(
                    Button("Reset OAuth Cache", id="reset-oauth-cache-button", variant="error"),
                    classes="oauth-grid",
                )

    def reload_from_config(self) -> None:
        option_list = self.query_one("#oauth-site-list", OptionList)
        option_list.clear_options()
        labels = oauth_option_labels()
        if labels:
            option_list.add_options(labels)
            option_list.highlighted = 0

    ############################ Config ############################

    @on(Button.Pressed, "#refresh-config-button")
    @on(Button.Pressed, "#update-refresh-config-button")
    def on_refresh_config_pressed(self, event: Button.Pressed) -> None:
        reload_config_from_disk(self)

    @on(Button.Pressed, "#edit-config-button")
    def on_edit_config_pressed(self, event: Button.Pressed) -> None:
        open_editor_path(self, BATCHGDL_CONFIG_PATH)

    @on(Button.Pressed, "#edit-gdl-config-button")
    def on_edit_gdl_config_pressed(self, event: Button.Pressed) -> None:
        open_editor_path(self, config_file_path())

    @on(Button.Pressed, "#open-log-file-button")
    def on_open_log_file_pressed(self, event: Button.Pressed) -> None:
        open_editor_path(self, config["log_file"])

    @on(Button.Pressed, "#delete-trashed-lists-button")
    def on_delete_trashed_lists_pressed(self, event: Button.Pressed) -> None:
        self.app.push_screen(ClearTrashModal())

    ############################ Update ############################

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

    ############################ OAuth ############################

    def selected_oauth_sites(self) -> list[str]:
        option = self.query_one("#oauth-site-list", OptionList).highlighted_option
        if option is None:
            return []
        prompt = str(option.prompt).strip()
        if prompt == _OAUTH_ALL_SITES:
            return oauth_sites()
        return [prompt]

    @on(Button.Pressed, "#reset-oauth-cache-button")
    def on_reset_oauth_cache_pressed(self, event: Button.Pressed) -> None:
        sites = self.selected_oauth_sites()
        if not sites:
            self.notify("Nothing configured or selected.", severity="warning")
            return

        self.notify("Starting OAuth reset in a new terminal…", severity="information")
        spawn_new_console(build_oauth_reset_command(sites, gdl_config=config_file_path()))
