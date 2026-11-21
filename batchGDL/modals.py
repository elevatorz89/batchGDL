import os

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll, ItemGrid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input

from .config import config, save_config, entry_extra_flags, job_section, with_optional_flags
from .constants import APPEND_LISTS_DIR, SINGLE_LISTS_DIR, SUBSCRIPTION_LISTS_DIR
from .lists import (
    append_list_name, slug_list_name, lists_txt_path, ensure_or_rename_list_txt,
)
from .system import move_to_trash, clear_list_trash

_MODAL_SCROLL = "list-modal list-modal-scroll"

LIST_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("Display name", "display-name", "Display name..."),
    ("List filename", "list-file", "Defaults to display name"),
    ("Destination folder", "dest-folder", "Defaults to list filename"),
    ("Extra flags", "extra-flags", 'Optional, e.g. --write-metadata --filter "score > 10"'),
)

SUBSCRIPTION_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("Display name", "display-name", "My Subscription"),
    ("List filename", "list-file", "Defaults to display name"),
    ("Destination folder", "dest-folder", "Defaults to list filename"),
    ("Archive filename", "archive-file", "Required"),
    ("Extra flags", "extra-flags", 'Optional, e.g. --write-metadata --filter "score > 10"'),
)


def list_initial_values(original_name: str | None) -> dict[str, str]:
    if not original_name:
        return {}
    entry = job_section("single").get(original_name)
    if not entry or len(entry) < 2:
        return {"display-name": original_name}
    return {
        "display-name": original_name,
        "list-file": entry[0],
        "dest-folder": entry[1],
        "extra-flags": entry_extra_flags(entry, 2),
    }


def subscription_initial_values(original_name: str | None) -> dict[str, str]:
    if not original_name:
        return {}
    entry = job_section("subscription").get(original_name)
    if not entry or len(entry) < 2:
        return {"display-name": original_name}
    return {
        "display-name": original_name,
        "dest-folder": entry[0],
        "list-file": entry[1],
        "archive-file": entry[2] if len(entry) > 2 else "",
        "extra-flags": entry_extra_flags(entry, 3),
    }


def build_list_entry(values: dict[str, str]) -> list[str]:
    display_name = values["display-name"]
    list_file = slug_list_name(values.get("list-file", "") or display_name)
    dest_folder = slug_list_name(values.get("dest-folder", "") or list_file)
    return with_optional_flags([list_file, dest_folder], values.get("extra-flags", ""))


def build_subscription_entry(values: dict[str, str]) -> list[str] | None:
    display_name = values["display-name"]
    list_file = slug_list_name(values.get("list-file", "") or display_name)
    dest_folder = slug_list_name(values.get("dest-folder", "") or list_file)
    archive_file = values.get("archive-file", "")
    if not archive_file:
        return None
    return with_optional_flags(
        [dest_folder, list_file, slug_list_name(archive_file)],
        values.get("extra-flags", ""),
    )


def list_file_from_values(values: dict[str, str]) -> str | None:
    display_name = values.get("display-name", "")
    list_file = values.get("list-file", "")
    if not (display_name or list_file):
        return None
    return slug_list_name(list_file or display_name)


def list_file_from_entry(section: str, entry: list) -> str | None:
    index_by_section = {"single": 0, "subscription": 1}
    index = index_by_section.get(section)
    if index is None:
        return None
    return entry[index] if len(entry) > index else None


def save_job_entry(
    *,
    section: str,
    lists_dir: str,
    original_name: str | None,
    values: dict[str, str],
    entry: list[str],
) -> str:
    # returns saved display name
    display_name = values["display-name"]
    section_data = job_section(section)

    old_list_file = None
    if original_name and original_name in section_data:
        old_list_file = list_file_from_entry(section, section_data[original_name])

    new_list_file = list_file_from_values(values)
    if new_list_file:
        ensure_or_rename_list_txt(old_list_file, new_list_file, lists_dir)
        if section == "subscription" and old_list_file:
            # Keep the subscription's append list (if it has one) matched to its list file.
            ensure_or_rename_list_txt(
                append_list_name(old_list_file),
                append_list_name(new_list_file),
                APPEND_LISTS_DIR,
                create_if_missing=False,
            )

    if original_name and original_name != display_name:
        section_data.pop(original_name, None)
    section_data[display_name] = entry
    save_config()
    return display_name


def global_flags_value(config_key: str) -> str:
    flags = config.get(config_key) or []
    if isinstance(flags, str):
        return flags
    return " ".join(str(flag) for flag in flags)


def save_global_flags(config_key: str, value: str) -> None:
    value = value.strip().replace('"', "'")
    config[config_key] = [value] if value else []
    save_config()


def compose_entry_fields(
    fields: tuple[tuple[str, str, str], ...],
    *,
    values: dict[str, str] | None = None,
    id_prefix: str = "",
) -> ComposeResult:
    values = values or {}
    for label, input_id, placeholder in fields:
        yield Label(label)
        yield Input(
            value=values.get(input_id, ""),
            id=f"{id_prefix}{input_id}" if id_prefix else input_id,
            placeholder=placeholder,
        )


def compose_entry_form(title: str, fields: tuple[tuple[str, str, str], ...]) -> ComposeResult:
    with VerticalScroll(classes=_MODAL_SCROLL):
        yield Label(title, classes="list-modal-title")
        yield from compose_entry_fields(fields)
        yield Label("", id="entry-error", classes="list-modal-error")
        with ItemGrid(classes="list-modal-actions", min_column_width=14):
            yield Button("Add", id="entry-confirm", variant="primary")
            yield Button("Cancel", id="entry-cancel")


class EntryModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]
    _FIELDS: tuple[tuple[str, str, str], ...] = ()
    _TITLE = "Add"
    _CONFIG_SECTION = ""
    _LISTS_DIR = SUBSCRIPTION_LISTS_DIR

    def build_entry(self, values: dict[str, str], error: Label) -> list[str] | None:
        raise NotImplementedError

    def compose(self) -> ComposeResult:
        yield from compose_entry_form(self._TITLE, self._FIELDS)

    def on_mount(self) -> None:
        self.query_one("#display-name", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(False)

    def _field_values(self) -> dict[str, str]:
        return {
            input_id: self.query_one(f"#{input_id}", Input).value.strip()
            for _, input_id, _ in self._FIELDS
        }

    @on(Button.Pressed, "#entry-cancel")
    def on_cancel_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(False)

    @on(Input.Submitted)
    @on(Button.Pressed, "#entry-confirm")
    def on_submit(self, event: object) -> None:
        self._submit()

    def _submit(self) -> None:
        error = self.query_one("#entry-error", Label)
        values = self._field_values()
        display_name = values.get("display-name", "")
        if not display_name:
            error.update("Display name is required.")
            return

        section = job_section(self._CONFIG_SECTION)
        if display_name in section:
            kind = "subscription" if self._CONFIG_SECTION == "subscription" else "list"
            error.update(f"A {kind} with that display name already exists.")
            return

        entry = self.build_entry(values, error)
        if entry is None:
            return

        save_job_entry(
            section=self._CONFIG_SECTION,
            lists_dir=self._LISTS_DIR,
            original_name=None,
            values=values,
            entry=entry,
        )
        self.dismiss(True)


class ListModal(EntryModal):
    _FIELDS = LIST_FIELDS
    _TITLE = "Add List"
    _CONFIG_SECTION = "single"
    _LISTS_DIR = SINGLE_LISTS_DIR

    def build_entry(self, values: dict[str, str], error: Label) -> list[str] | None:
        return build_list_entry(values)


class SubscriptionModal(EntryModal):
    _FIELDS = SUBSCRIPTION_FIELDS
    _TITLE = "Add Subscription"
    _CONFIG_SECTION = "subscription"
    _LISTS_DIR = SUBSCRIPTION_LISTS_DIR

    def build_entry(self, values: dict[str, str], error: Label) -> list[str] | None:
        entry = build_subscription_entry(values)
        if entry is None:
            error.update("Archive filename is required.")
        return entry


class DeleteEntryModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(
        self,
        title: str,
        item_name: str,
        config_section: str,
        *,
        note: str = "The list file on disk is kept.",
        list_file: str | None = None,
        trash_list_file: bool = False,
        lists_dir: str = SUBSCRIPTION_LISTS_DIR,
    ) -> None:
        super().__init__()
        self.title_text = title
        self.item_name = item_name
        self.config_section = config_section
        self.note = note
        self.list_file = list_file
        self.trash_list_file = trash_list_file
        self.lists_dir = lists_dir

    def compose(self) -> ComposeResult:
        with Vertical(classes="list-modal"):
            yield Label(self.title_text, classes="list-modal-title")
            yield Label(f'Delete "{self.item_name}" from the app?')
            yield Label(self.note, classes="list-modal-note")
            with ItemGrid(classes="list-modal-actions", min_column_width=14):
                yield Button("Delete", id="delete-entry-confirm", variant="error")
                yield Button("Cancel", id="delete-entry-cancel")

    def action_cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#delete-entry-cancel")
    def on_cancel_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#delete-entry-confirm")
    def on_confirm_pressed(self, event: Button.Pressed) -> None:
        if self.trash_list_file and self.list_file:
            path = lists_txt_path(self.list_file, self.lists_dir)
            if os.path.isfile(path):
                try:
                    move_to_trash(path)
                except OSError as e:
                    self.app.notify(f"Could not move list file to trash: {e}", severity="error")
                    return
            if self.config_section == "subscription":
                # If the append list could not be moved to the trash, notify the user.
                append_path = lists_txt_path(append_list_name(self.list_file), APPEND_LISTS_DIR)
                if os.path.isfile(append_path):
                    try:
                        move_to_trash(append_path)
                    except OSError as e:
                        self.app.notify(
                            f"Could not move append list to trash ({e}). It was left in {APPEND_LISTS_DIR}.",
                            severity="warning",
                        )

        job_section(self.config_section).pop(self.item_name, None)
        save_config()
        self.dismiss(True)


class ClearTrashModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="list-modal"):
            yield Label("Delete Trashed Lists", classes="list-modal-title")
            yield Label(f"Permanently delete all trashed list files?")
            yield Label("This cannot be undone.", classes="list-modal-note")
            with ItemGrid(classes="list-modal-actions", min_column_width=14):
                yield Button("Delete", id="clear-trash-confirm", variant="error")
                yield Button("Cancel", id="clear-trash-cancel")

    def action_cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#clear-trash-cancel")
    def on_cancel_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#clear-trash-confirm")
    def on_confirm_pressed(self, event: Button.Pressed) -> None:
        try:
            removed = clear_list_trash()
        except OSError as e:
            self.app.notify(f"Could not delete trashed lists: {e}", severity="error")
            return
        if removed:
            self.app.notify(f"Deleted {removed} trashed list(s).", severity="information")
        else:
            self.app.notify("No trashed lists to delete.", severity="information")
        self.dismiss(True)