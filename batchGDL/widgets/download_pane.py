import os

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ItemGrid, Vertical
from textual.widgets import Button, Label, Markdown, Static, Switch, TabbedContent, TabPane

from ..config import (
    flags_without_option, global_flags_string, job_section,
    single_list_entry, subscription_entry,
)
from ..constants import APPEND_LISTS_DIR, SINGLE_LISTS_DIR, SUBSCRIPTION_LISTS_DIR
from ..downloads import build_command, build_download_all_command, build_download_job_command, log_download_job
from ..lists import append_list_name, ensure_list_txt, list_file_is_empty, lists_txt_path
from ..system import spawn_new_console
from .common import DOWNLOAD_ALL_LABEL, open_editor_path


class DownloadPane(Vertical):

    def __init__(self) -> None:
        super().__init__(id="download-pane")
        self._kind: str | None = None
        self._name: str | None = None

    def compose(self) -> ComposeResult:
        with TabbedContent(id="download-tabs"):
            with TabPane("Downloader", id="download-main-tab"):
                yield Markdown("Selected list:")
                yield Label("", id="download-selection")
                yield ItemGrid(
                    Button("Download", id="download-button", variant="primary", disabled=True),
                    classes="list-actions",
                    min_column_width=14,
                )
            with TabPane("Append", id="download-append-tab"):
                yield Markdown(
                    "Downloads from this tab will only include links in the below append list and ignore date filters. "
                    "If you wish to download absolutely everything even if it's been downloaded before, toggle the ignore switch below."
                )
                yield Horizontal(
                    Static("Ignore archive: ", classes="ignore-archive-label"),
                    Switch(id="ignore-archive"),
                    classes="subs-horizontal",
                )
                yield ItemGrid(
                    Button("Edit Append List", id="edit-append-list-button"),
                    classes="subs-actions",
                    min_column_width=16,
                )
                yield ItemGrid(
                    Button("Download (Append)", id="download-append-button", variant="primary"),
                    classes="subs-actions",
                    min_column_width=16,
                )

    ############################ Selection ############################

    def set_selection(self, kind: str | None, name: str | None, *, reset_options: bool = True) -> None:
        self._kind = kind
        self._name = name
        self.query_one("#download-button", Button).disabled = not (kind and name)
        self.query_one("#download-selection", Label).update(name or "")

        # forces ignore archive to be toggled off when picking a different entry
        if reset_options:
            self.query_one("#ignore-archive", Switch).value = False

        # locks append tab for single lists and the download all screen
        tabs = self.query_one("#download-tabs", TabbedContent)
        if kind == "single" or (kind == "subscription" and name == DOWNLOAD_ALL_LABEL):
            tabs.active = "download-main-tab"
            tabs.disable_tab("download-append-tab")
        else:
            tabs.enable_tab("download-append-tab")

    ############################ Append ############################

    def _append_target(self) -> tuple[str, tuple[str, str, str | None, str]] | None:
        # gets (name, subscription entry) for the selected subscription, or posts a warning if None.
        name = self._name
        if self._kind != "subscription" or not name or name == DOWNLOAD_ALL_LABEL:
            self.notify("Select a single subscription first.", severity="warning")
            return None
        subscription = subscription_entry(name)
        if not subscription:
            self.notify("Unknown subscription.", severity="warning")
            return None
        return name, subscription

    @on(Button.Pressed, "#edit-append-list-button")
    def on_edit_append_list_pressed(self, event: Button.Pressed) -> None:
        target = self._append_target()
        if not target:
            return
        _, (_, list_file, _, _) = target
        append_file = append_list_name(list_file)
        ensure_list_txt(append_file, APPEND_LISTS_DIR)
        open_editor_path(self, lists_txt_path(append_file, APPEND_LISTS_DIR))

    @on(Button.Pressed, "#download-append-button")
    def on_download_append_pressed(self, event: Button.Pressed) -> None:
        target = self._append_target()
        if not target:
            return
        name, (dest_folder, list_file, archive, extra_flags) = target
        append_file = append_list_name(list_file)
        if list_file_is_empty(append_file, APPEND_LISTS_DIR):
            self.notify(
                f'The append list for "{name}" is empty. Use "Edit Append List" to add links.',
                severity="warning",
            )
            return

        # Append downloads must not skip media, so drop the subscription's --filter.
        global_flags = flags_without_option(
            global_flags_string("global-flags-subscriptions"), "--filter"
        )
        use_archive = None if self.query_one("#ignore-archive", Switch).value else archive

        self._run_download(
            dest_folder=dest_folder,
            input_file=append_file,
            path_key="sub",
            archive=use_archive,
            lists_dir=APPEND_LISTS_DIR,
            global_flags=global_flags,
            extra_flags=extra_flags,
            job_name=f"{name} (append)",
            notify_message=f"Starting append download for {name}.",
        )

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
        if name == DOWNLOAD_ALL_LABEL:
            self._download_all_subscriptions()
            return

        subscription = subscription_entry(name)
        if not subscription:
            self.notify("Unknown subscription.", severity="warning")
            return

        dest_folder, list_file, archive, extra_flags = subscription
        if not self._require_nonempty_list(
            list_file, lists_dir=SUBSCRIPTION_LISTS_DIR, label=f'Subscription "{name}"'
        ):
            return

        self._run_download(
            dest_folder=dest_folder,
            input_file=list_file,
            path_key="sub",
            archive=archive,
            global_flags=global_flags_string("global-flags-subscriptions"),
            extra_flags=extra_flags,
            job_name=name,
            notify_message=f"Starting download for {name}.",
        )

    def _download_all_subscriptions(self) -> None:
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
