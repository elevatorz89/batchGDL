import os

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ItemGrid, Vertical
from textual.widgets import Button, Label, Markdown, Static, Switch, TabbedContent, TabPane

from ..config import (
    flags_without_option, global_flags_string, job_section,
    single_list_entry, subscription_entry,
)
from ..constants import SINGLE_LISTS_DIR, SUBSCRIPTION_LISTS_DIR
from ..downloads import build_command, build_download_all_command, build_download_job_command, log_download_job
from ..lists import ensure_list_txt, list_file_is_empty, lists_txt_path
from ..system import spawn_new_console
from .common import DOWNLOAD_ALL_LABEL, open_editor_path

_APPEND_LIST_NAME = "#append"


class DownloadPane(Vertical):

    def __init__(self) -> None:
        super().__init__(id="download-pane")
        self._kind: str | None = None
        self._name: str | None = None

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Downloader"):
                yield Markdown("Choose a list or subscription to download.")
                yield Label("", id="download-selection")
                yield ItemGrid(
                    Button("Download", id="download-button", variant="primary", disabled=True),
                    classes="list-actions",
                    min_column_width=14,
                )
            with TabPane("Append"):
                yield Markdown("Append mode applies to subscriptions.")
                yield Horizontal(
                    Static("Append Mode: ", classes="append-mode-label"),
                    Switch(id="append", disabled=True),
                    Static("Ignore archive: ", classes="ignore-archive-label"),
                    Switch(id="ignore-archive", disabled=True),
                    classes="subs-horizontal",
                )
                yield ItemGrid(
                    Button("Edit Append List", id="edit-append-list-button"),
                    classes="subs-actions",
                    min_column_width=16,
                )

    ############################ Selection ############################

    def set_selection(self, kind: str | None, name: str | None) -> None:
        self._kind = kind
        self._name = name
        self.query_one("#download-button", Button).disabled = not (kind and name)
        self.query_one("#download-selection", Label).update(name or "")

        append = self.query_one("#append", Switch)
        append.disabled = kind != "subscription"
        if append.disabled:
            append.value = False
        self._sync_ignore_archive_switch()

    def _sync_ignore_archive_switch(self) -> None:
        append_on = self.query_one("#append", Switch).value
        ignore_archive = self.query_one("#ignore-archive", Switch)
        if not append_on:
            ignore_archive.value = False
        ignore_archive.disabled = not append_on

    ############################ Append ############################

    @staticmethod
    def _ensure_append_list() -> None:
        ensure_list_txt(_APPEND_LIST_NAME, SUBSCRIPTION_LISTS_DIR)

    @on(Switch.Changed, "#append")
    def on_append_mode_changed(self, event: Switch.Changed) -> None:
        if event.value:
            self._ensure_append_list()
        self._sync_ignore_archive_switch()

    @on(Button.Pressed, "#edit-append-list-button")
    def on_edit_append_list_pressed(self, event: Button.Pressed) -> None:
        self._ensure_append_list()
        open_editor_path(self, lists_txt_path(_APPEND_LIST_NAME, SUBSCRIPTION_LISTS_DIR))

    ############################ Download ############################

    @on(Button.Pressed, "#download-button")
    def on_download_pressed(self, event: Button.Pressed) -> None:
        name = self._name
        if not self._kind or not name:
            self.notify("Select a list or subscription first.", severity="warning")
            return
        if self._kind == "single":
            self._download_single(name)
        else:
            self._download_subscription(name)

    def _require_nonempty_list(self, list_file: str, *, lists_dir: str, label: str) -> bool:
        if list_file_is_empty(list_file, lists_dir):
            self.notify(f"{label} is empty. There's nothing to download.", severity="warning")
            return False
        return True

    def _download_single(self, name: str) -> None:
        entry = single_list_entry(name)
        if not entry:
            self.notify(f"No list configured for: {name}", severity="warning")
            return
        list_file, dest_folder, extra_flags = entry
        if not self._require_nonempty_list(list_file, lists_dir=SINGLE_LISTS_DIR, label=f'List "{name}"'):
            return
        self._run_download(
            dest_folder=dest_folder,
            input_file=list_file,
            path_key="list",
            lists_dir=SINGLE_LISTS_DIR,
            global_flags=global_flags_string("global-flags-single"),
            extra_flags=extra_flags,
            job_name=name,
            notify_message=f"Starting download for {name} in a new terminal window.",
        )

    def _download_subscription(self, name: str) -> None:
        append = self.query_one("#append", Switch).value

        if name == DOWNLOAD_ALL_LABEL:
            self._download_all_subscriptions(append)
            return

        subscription = subscription_entry(name)
        if not subscription:
            self.notify("Unknown subscription.", severity="warning")
            return

        dest_folder, list_file, archive, extra_flags = subscription
        if append:
            self._ensure_append_list()
            input_file = _APPEND_LIST_NAME
            label = "Append list"
            job_name = f"{name} (append)"
        else:
            input_file = list_file
            label = f'Subscription "{name}"'
            job_name = name

        if not self._require_nonempty_list(input_file, lists_dir=SUBSCRIPTION_LISTS_DIR, label=label):
            return

        global_flags = global_flags_string("global-flags-subscriptions")
        if append:
            global_flags = flags_without_option(global_flags, "--filter")

        use_archive = archive
        if append and self.query_one("#ignore-archive", Switch).value:
            use_archive = None

        self._run_download(
            dest_folder=dest_folder,
            input_file=input_file,
            path_key="sub",
            archive=use_archive,
            global_flags=global_flags,
            extra_flags=extra_flags,
            job_name=job_name,
            notify_message=f"Starting download for {name}.",
        )

    def _download_all_subscriptions(self, append: bool) -> None:
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
            self.notify(f"Skipping {skipped} empty subscription list(s).", severity="warning")
        self.notify("Downloading from all lists in a new terminal…", severity="information")
        spawn_new_console(build_download_all_command(nonempty, work_dir=os.getcwd()), cwd=os.getcwd())

    def _run_download(
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
                title=f"batchGDL — {job_name}" if job_name else None,
            )
        )
