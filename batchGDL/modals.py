import os

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll, ItemGrid
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Input

from .config import config, save_config, entry_extra_flags, job_section, with_optional_flags
from .constants import SINGLE_LISTS_DIR, SUBSCRIPTION_LISTS_DIR
from .lists import slug_list_name, lists_txt_path, ensure_list_txt, ensure_or_rename_list_txt
from .system import open_editor, move_to_trash, clear_list_trash

_MODAL_SCROLL = "list-modal list-modal-scroll"

LIST_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("Display name", "display-name", "Display name..."),
    ("List filename", "list-file", "Defaults to display name"),
    ("Destination folder", "dest-folder", "Defaults to list filename"),
    ("Extra flags", "extra-flags", 'Optional, e.g. --write-metadata --filter "score > 10"'),
)

SUBSCRIPTION_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("Display name", "display-name", "My Subscription"),
    ("Category folder", "category", "Defaults to display name"),
    ("List filename", "list-file", "Defaults to display name"),
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
        "category": entry[0],
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
    slug = slug_list_name(display_name)
    category = slug_list_name(values.get("category", "") or slug)
    list_file = slug_list_name(values.get("list-file", "") or slug)
    archive_file = values.get("archive-file", "")
    if not archive_file:
        return None
    return with_optional_flags(
        [category, list_file, slug_list_name(archive_file)],
        values.get("extra-flags", ""),
    )


def list_file_from_values(section: str, values: dict[str, str]) -> str | None:
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
    """Persist a job entry and return the saved display name."""
    display_name = values["display-name"]
    section_data = job_section(section)

    old_list_file = None
    if original_name and original_name in section_data:
        old_list_file = list_file_from_entry(section, section_data[original_name])

    new_list_file = list_file_from_values(section, values)
    if new_list_file:
        ensure_or_rename_list_txt(old_list_file, new_list_file, lists_dir)

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


def compose_entry_form(
    title: str,
    fields: tuple[tuple[str, str, str], ...],
    *,
    confirm_label: str,
    values: dict[str, str] | None = None,
    show_open_list: bool = False,
) -> ComposeResult:
    with VerticalScroll(classes=_MODAL_SCROLL):
        yield Label(title, classes="list-modal-title")
        yield from compose_entry_fields(fields, values=values)
        yield Label("", id="entry-error", classes="list-modal-error")
        with ItemGrid(classes="list-modal-actions", min_column_width=14):
            yield Button(confirm_label, id="entry-confirm", variant="primary")
            if show_open_list:
                yield Button("Open list file", id="entry-open-list")
            yield Button("Cancel", id="entry-cancel")


class EntryModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]
    _FIELDS: tuple[tuple[str, str, str], ...] = ()
    _TITLE_ADD = "Add"
    _TITLE_EDIT = "Edit"
    _CONFIG_SECTION = ""
    _LISTS_DIR = SUBSCRIPTION_LISTS_DIR

    def __init__(self, *, original_name: str | None = None) -> None:
        super().__init__()
        self.original_name = original_name
        self.editing = original_name is not None

    def initial_values(self) -> dict[str, str]:
        return {}

    def list_file_from_values(self, values: dict[str, str]) -> str | None:
        return list_file_from_values(self._CONFIG_SECTION, values)

    def list_file_from_entry(self, entry: list) -> str | None:
        return list_file_from_entry(self._CONFIG_SECTION, entry)

    def build_entry(self, values: dict[str, str], error: Label) -> list[str] | None:
        raise NotImplementedError

    def compose(self) -> ComposeResult:
        yield from compose_entry_form(
            self._TITLE_EDIT if self.editing else self._TITLE_ADD,
            self._FIELDS,
            confirm_label="Save" if self.editing else "Add",
            values=self.initial_values() if self.editing else None,
            show_open_list=self.editing,
        )

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

    @on(Button.Pressed, "#entry-open-list")
    def on_open_list_pressed(self, event: Button.Pressed) -> None:
        list_file = self.list_file_from_values(self._field_values())
        if not list_file and self.original_name:
            entry = job_section(self._CONFIG_SECTION).get(self.original_name)
            if entry:
                list_file = self.list_file_from_entry(entry)
        if not list_file:
            self.app.notify("No list file to open.", severity="warning")
            return
        ensure_list_txt(list_file, self._LISTS_DIR)
        open_editor(os.path.abspath(lists_txt_path(list_file, self._LISTS_DIR)))

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
        if display_name in section and display_name != self.original_name:
            kind = "subscription" if self._CONFIG_SECTION == "subscription" else "list"
            error.update(f"A {kind} with that display name already exists.")
            return

        entry = self.build_entry(values, error)
        if entry is None:
            return

        save_job_entry(
            section=self._CONFIG_SECTION,
            lists_dir=self._LISTS_DIR,
            original_name=self.original_name,
            values=values,
            entry=entry,
        )
        self.dismiss(True)


class ListModal(EntryModal):
    _FIELDS = LIST_FIELDS
    _TITLE_ADD = "Add List"
    _TITLE_EDIT = "Edit List"
    _CONFIG_SECTION = "single"
    _LISTS_DIR = SINGLE_LISTS_DIR

    def initial_values(self) -> dict[str, str]:
        return list_initial_values(self.original_name)

    def build_entry(self, values: dict[str, str], error: Label) -> list[str] | None:
        return build_list_entry(values)


class SubscriptionModal(EntryModal):
    _FIELDS = SUBSCRIPTION_FIELDS
    _TITLE_ADD = "Add Subscription"
    _TITLE_EDIT = "Edit Subscription"
    _CONFIG_SECTION = "subscription"
    _LISTS_DIR = SUBSCRIPTION_LISTS_DIR

    def initial_values(self) -> dict[str, str]:
        return subscription_initial_values(self.original_name)

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


class GlobalFlagsModal(ModalScreen[bool]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, config_key: str, title: str) -> None:
        super().__init__()
        self.config_key = config_key
        self.title_text = title

    def _flags_value(self) -> str:
        return global_flags_value(self.config_key)

    def compose(self) -> ComposeResult:
        with VerticalScroll(classes=_MODAL_SCROLL):
            yield Label(self.title_text, classes="list-modal-title")
            yield Label("Global flags")
            yield Input(
                value=self._flags_value(),
                id="global-flags",
                placeholder='e.g. --cookies-from-browser firefox',
            )
            with ItemGrid(classes="list-modal-actions", min_column_width=14):
                yield Button("Save", id="global-flags-confirm", variant="primary")
                yield Button("Cancel", id="global-flags-cancel")

    def on_mount(self) -> None:
        self.query_one("#global-flags", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#global-flags-cancel")
    def on_cancel_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(False)

    @on(Input.Submitted, "#global-flags")
    @on(Button.Pressed, "#global-flags-confirm")
    def on_submit(self, event: object) -> None:
        save_global_flags(self.config_key, self.query_one("#global-flags", Input).value)
        self.dismiss(True)
