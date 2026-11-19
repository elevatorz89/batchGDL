import json
import os

from textual.message import Message
from textual.widget import Widget

from ..config import BATCHGDL_CONFIG_PATH, reload_config
from ..system import open_editor

DOWNLOAD_ALL_LABEL = "-Download All-"


class ConfigChanged(Message):
    # posts after config or list entries get changed.
    pass


def open_editor_path(widget: Widget, path: str) -> None:
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        widget.notify(f"File not found: {path}", severity="warning")
        return
    try:
        open_editor(path)
    except OSError as e:
        widget.notify(f"Could not open file: {e}", severity="error")


def reload_config_from_disk(widget: Widget) -> None:
    if not os.path.isfile(BATCHGDL_CONFIG_PATH):
        widget.notify(f"File not found: {BATCHGDL_CONFIG_PATH}", severity="warning")
        return
    try:
        reload_config()
    except json.JSONDecodeError as e:
        widget.notify(f"Invalid config JSON: {e}", severity="error")
        return
    except (OSError, KeyError) as e:
        widget.notify(f"Failed to load config: {e}", severity="error")
        return

    widget.post_message(ConfigChanged())
    widget.notify("Config reloaded.", severity="information")
