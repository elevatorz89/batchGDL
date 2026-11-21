from textual import on
from textual.app import ComposeResult
from textual.containers import ItemGrid, Vertical, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import (
    Button, ContentSwitcher, Input, Label, Markdown, TabbedContent, TabPane,
)

from ..config import job_section, single_list_entry, subscription_entry
from ..constants import SINGLE_LISTS_DIR, SUBSCRIPTION_LISTS_DIR
from ..lists import ensure_list_txt, lists_txt_path
from ..modals import (
    DeleteEntryModal,
    LIST_FIELDS, SUBSCRIPTION_FIELDS,
    list_initial_values, subscription_initial_values,
    build_list_entry, build_subscription_entry,
    list_file_from_values, list_file_from_entry,
    save_job_entry, global_flags_value, save_global_flags, compose_entry_fields,
)
from .common import DOWNLOAD_ALL_LABEL, open_editor_path

_EDIT_SINGLE_PREFIX = "edit-single-"
_EDIT_SUB_PREFIX = "edit-sub-"
_GLOBAL_FLAGS_SINGLE = "global-flags-single"
_GLOBAL_FLAGS_SUBSCRIPTIONS = "global-flags-subscriptions"


class EditPane(Widget):

    BORDER_TITLE = "Edit"

    class Saved(Message):

        def __init__(self, kind: str, name: str) -> None:
            super().__init__()
            self.kind = kind
            self.name = name

    class Deleted(Message):
        # triggers on deleted lists
        pass

    def __init__(self) -> None:
        super().__init__(id="edit-pane")
        self._kind: str | None = None
        self._name: str | None = None

    def compose(self) -> ComposeResult:
        with TabbedContent(id="edit-tabs"):
            with TabPane("Edit List", id="edit-list-tab"):
                with VerticalScroll(classes="edit-pane-scroll"):
                    with ContentSwitcher(initial="edit-list-empty", id="edit-list-switcher"):
                        with Vertical(id="edit-list-empty"):
                            yield Markdown("Select a list or subscription to edit.")
                        with Vertical(id="edit-list-single"):
                            yield from compose_entry_fields(
                                LIST_FIELDS, id_prefix=_EDIT_SINGLE_PREFIX
                            )
                        with Vertical(id="edit-list-subscription"):
                            yield from compose_entry_fields(
                                SUBSCRIPTION_FIELDS, id_prefix=_EDIT_SUB_PREFIX
                            )
                    yield Label("", id="edit-list-error", classes="list-modal-error")
                    yield ItemGrid(
                        Button("Save", id="edit-list-save", variant="primary"),
                        Button("Reset", id="edit-list-reset"),
                        Button("Open list file", id="edit-list-open"),
                        classes="list-modal-actions",
                        min_column_width=14,
                    )
                    yield ItemGrid(
                        Button("Delete List", id="edit-delete-list", variant="error"),
                        classes="list-actions",
                        min_column_width=14,
                    )
            with TabPane("Edit Global Flags", id="edit-flags-tab"):
                with VerticalScroll(classes="edit-pane-scroll"):
                    yield Label("", id="edit-flags-title", classes="list-modal-title")
                    yield Label("Global flags")
                    yield Input(
                        id="edit-global-flags",
                        placeholder='e.g. --cookies-from-browser firefox',
                    )
                    yield ItemGrid(
                        Button("Save", id="edit-flags-save", variant="primary"),
                        Button("Reset", id="edit-flags-reset"),
                        classes="list-modal-actions",
                        min_column_width=14,
                    )

    def on_mount(self) -> None:
        self.clear_selection()

    @property
    def flags_config_key(self) -> str | None:
        if self._kind == "single":
            return _GLOBAL_FLAGS_SINGLE
        if self._kind == "subscription":
            return _GLOBAL_FLAGS_SUBSCRIPTIONS
        return None

    def clear_selection(self) -> None:
        self._kind = None
        self._name = None
        self.query_one("#edit-list-switcher", ContentSwitcher).current = "edit-list-empty"
        self._set_list_error("")
        self.query_one("#edit-flags-title", Label).update("Edit Global Flags")
        self.query_one("#edit-global-flags", Input).value = ""
        self._set_edit_enabled(False)

    def load_selection(self, kind: str, name: str) -> None:
        if kind == "subscription" and name == DOWNLOAD_ALL_LABEL:
            self._kind = "subscription"
            self._name = None
            self.query_one("#edit-list-switcher", ContentSwitcher).current = "edit-list-empty"
            self._set_list_error("")
            self._load_global_flags()
            self._set_edit_enabled(flags_only=True)
            return

        self._kind = kind
        self._name = name
        self._set_list_error("")
        if kind == "single":
            self.query_one("#edit-list-switcher", ContentSwitcher).current = "edit-list-single"
            self._set_field_values(LIST_FIELDS, _EDIT_SINGLE_PREFIX, list_initial_values(name))
        else:
            self.query_one("#edit-list-switcher", ContentSwitcher).current = "edit-list-subscription"
            self._set_field_values(
                SUBSCRIPTION_FIELDS, _EDIT_SUB_PREFIX, subscription_initial_values(name)
            )
        self._load_global_flags()
        self._set_edit_enabled(True)

    def reload_from_config(self) -> None:
        if self._kind and self._name:
            self.load_selection(self._kind, self._name)
        elif self._kind == "subscription":
            self.load_selection("subscription", DOWNLOAD_ALL_LABEL)
        else:
            self.clear_selection()

    def _set_edit_enabled(self, enabled: bool = True, *, flags_only: bool = False) -> None:
        list_enabled = enabled and not flags_only
        flags_enabled = enabled or flags_only
        for button_id in ("#edit-list-save", "#edit-list-reset", "#edit-list-open", "#edit-delete-list"):
            self.query_one(button_id, Button).disabled = not list_enabled
        for button_id in ("#edit-flags-save", "#edit-flags-reset"):
            self.query_one(button_id, Button).disabled = not flags_enabled

        # locks list tab for download all screen
        tabs = self.query_one("#edit-tabs", TabbedContent)
        if flags_only:
            tabs.active = "edit-flags-tab"
            tabs.disable_tab("edit-list-tab")
        else:
            tabs.enable_tab("edit-list-tab")

    def _set_list_error(self, message: str) -> None:
        # Hidden while empty so it doesn't add a blank row above the buttons.
        label = self.query_one("#edit-list-error", Label)
        label.update(message)
        label.display = bool(message)
    def _set_field_values(
        self,
        fields: tuple[tuple[str, str, str], ...],
        prefix: str,
        values: dict[str, str],
    ) -> None:
        for _, input_id, _ in fields:
            self.query_one(f"#{prefix}{input_id}", Input).value = values.get(input_id, "")

    def _field_values(
        self,
        fields: tuple[tuple[str, str, str], ...],
        prefix: str,
    ) -> dict[str, str]:
        return {
            input_id: self.query_one(f"#{prefix}{input_id}", Input).value.strip()
            for _, input_id, _ in fields
        }

    def _load_global_flags(self) -> None:
        key = self.flags_config_key
        title = self.query_one("#edit-flags-title", Label)
        flags_input = self.query_one("#edit-global-flags", Input)
        if key == _GLOBAL_FLAGS_SINGLE:
            title.update("Edit Global Flags (Single)")
            flags_input.value = global_flags_value(key)
        elif key == _GLOBAL_FLAGS_SUBSCRIPTIONS:
            title.update("Edit Global Flags (Subscriptions)")
            flags_input.value = global_flags_value(key)
        else:
            title.update("Edit Global Flags")
            flags_input.value = ""

    def save_list(self) -> str | None:
        if not self._kind or not self._name:
            self.notify("Select a list or subscription to edit.", severity="warning")
            return None

        if self._kind == "single":
            fields, prefix, lists_dir, section = LIST_FIELDS, _EDIT_SINGLE_PREFIX, SINGLE_LISTS_DIR, "single"
            values = self._field_values(fields, prefix)
            entry = build_list_entry(values) if values.get("display-name") else None
        else:
            fields, prefix, lists_dir, section = (
                SUBSCRIPTION_FIELDS, _EDIT_SUB_PREFIX, SUBSCRIPTION_LISTS_DIR, "subscription"
            )
            values = self._field_values(fields, prefix)
            entry = build_subscription_entry(values) if values.get("display-name") else None

        display_name = values.get("display-name", "")
        if not display_name:
            self._set_list_error("Display name is required.")
            return None

        section_data = job_section(section)
        if display_name in section_data and display_name != self._name:
            kind = "subscription" if section == "subscription" else "list"
            self._set_list_error(f"A {kind} with that display name already exists.")
            return None

        if entry is None:
            if section == "subscription":
                self._set_list_error("Archive filename is required.")
            else:
                self._set_list_error("Could not build list entry.")
            return None

        self._set_list_error("")
        saved_name = save_job_entry(
            section=section,
            lists_dir=lists_dir,
            original_name=self._name,
            values=values,
            entry=entry,
        )
        self._name = saved_name
        return saved_name

    def reset_list(self) -> None:
        if not self._kind or not self._name:
            return
        self._set_list_error("")
        if self._kind == "single":
            self._set_field_values(LIST_FIELDS, _EDIT_SINGLE_PREFIX, list_initial_values(self._name))
        else:
            self._set_field_values(
                SUBSCRIPTION_FIELDS, _EDIT_SUB_PREFIX, subscription_initial_values(self._name)
            )

    def save_flags(self) -> bool:
        key = self.flags_config_key
        if not key:
            self.notify("Select a list or subscription first.", severity="warning")
            return False
        save_global_flags(key, self.query_one("#edit-global-flags", Input).value)
        return True

    def reset_flags(self) -> None:
        self._load_global_flags()

    def open_list_file(self) -> None:
        if not self._kind or not self._name:
            self.notify("Select a list or subscription first.", severity="warning")
            return
        if self._kind == "single":
            values = self._field_values(LIST_FIELDS, _EDIT_SINGLE_PREFIX)
            lists_dir = SINGLE_LISTS_DIR
            section = "single"
        else:
            values = self._field_values(SUBSCRIPTION_FIELDS, _EDIT_SUB_PREFIX)
            lists_dir = SUBSCRIPTION_LISTS_DIR
            section = "subscription"

        list_file = list_file_from_values(values)
        if not list_file:
            entry = job_section(section).get(self._name)
            if entry:
                list_file = list_file_from_entry(section, entry)
        if not list_file:
            self.notify("No list file to open.", severity="warning")
            return
        ensure_list_txt(list_file, lists_dir)
        open_editor_path(self, lists_txt_path(list_file, lists_dir))

    ############################ Button handlers ############################

    @on(Button.Pressed, "#edit-list-save")
    def on_edit_list_save_pressed(self, event: Button.Pressed) -> None:
        saved_name = self.save_list()
        if not saved_name or not self._kind:
            return
        self.post_message(self.Saved(self._kind, saved_name))
        self.notify("List updated.", severity="information")

    @on(Button.Pressed, "#edit-list-reset")
    def on_edit_list_reset_pressed(self, event: Button.Pressed) -> None:
        self.reset_list()
        self.notify("List fields reset from config.", severity="information")

    @on(Button.Pressed, "#edit-list-open")
    def on_edit_list_open_pressed(self, event: Button.Pressed) -> None:
        self.open_list_file()

    @on(Button.Pressed, "#edit-flags-save")
    def on_edit_flags_save_pressed(self, event: Button.Pressed) -> None:
        if self.save_flags():
            self.notify("Global flags updated.", severity="information")

    @on(Button.Pressed, "#edit-flags-reset")
    def on_edit_flags_reset_pressed(self, event: Button.Pressed) -> None:
        self.reset_flags()
        self.notify("Global flags reset from config.", severity="information")

    @on(Button.Pressed, "#edit-delete-list")
    def on_edit_delete_list_pressed(self, event: Button.Pressed) -> None:
        kind, name = self._kind, self._name
        if not kind or not name:
            self.notify("Select a list or subscription to delete.", severity="warning")
            return
        if kind == "single":
            entry = single_list_entry(name)
            modal = self._delete_modal(
                "Delete List", name, "single", entry[0] if entry else None, SINGLE_LISTS_DIR
            )
        else:
            entry = subscription_entry(name)
            modal = self._delete_modal(
                "Delete Subscription", name, "subscription", entry[1] if entry else None,
                SUBSCRIPTION_LISTS_DIR,
            )
        self.app.push_screen(modal, self._after_delete)

    @staticmethod
    def _delete_modal(
        title: str, name: str, section: str, list_file: str | None, lists_dir: str
    ) -> DeleteEntryModal:
        return DeleteEntryModal(
            title,
            name,
            section,
            note="The list file will be moved to the list trash folder.",
            list_file=list_file,
            trash_list_file=True,
            lists_dir=lists_dir,
        )

    def _after_delete(self, result: bool | None) -> None:
        if not result:
            return
        self.post_message(self.Deleted())
        self.notify("List removed and file sent to trash.", severity="information")
