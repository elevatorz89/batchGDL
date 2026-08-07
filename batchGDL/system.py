import os
import sys
import shutil
import subprocess

from .constants import TRASH_LISTS_DIR


def open_editor(path: str) -> None:
    path = os.path.abspath(path)
    if sys.platform.startswith("darwin"):
        subprocess.Popen(
            ["open", path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    elif os.name == "nt":
        # weird workaround to stop output(?) text from appearing in the terminal
        subprocess.Popen(
            ["cmd", "/c", "start", "", path],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        opener = shutil.which("xdg-open") or shutil.which("gio")
        if not opener:
            raise OSError("No suitable file opener found for this platform")
        subprocess.Popen(
            [opener, path],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def move_to_trash(path: str) -> None:
    path = os.path.abspath(path)
    if not os.path.lexists(path):
        return

    trash_dir = os.path.abspath(TRASH_LISTS_DIR)
    os.makedirs(trash_dir, exist_ok=True)

    filename = os.path.basename(path)
    destination = os.path.join(trash_dir, filename)
    if os.path.lexists(destination):
        stem, extension = os.path.splitext(filename)
        suffix = 1
        while True:
            candidate = os.path.join(trash_dir, f"{stem}_{suffix}{extension}")
            if not os.path.lexists(candidate):
                destination = candidate
                break
            suffix += 1

    shutil.move(path, destination)


def clear_list_trash() -> int:
    trash_dir = os.path.abspath(TRASH_LISTS_DIR)
    if not os.path.isdir(trash_dir):
        return 0

    removed = 0
    with os.scandir(trash_dir) as entries:
        for entry in entries:
            if not entry.is_file(follow_symlinks=False) and not entry.is_symlink():
                continue
            os.unlink(entry.path)
            removed += 1
    return removed


def _new_console_process(command: list[str], *, cwd: str | None = None) -> subprocess.Popen:
    return subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=cwd)


def spawn_new_console(command: list[str], *, cwd: str | None = None) -> None:
    _new_console_process(command, cwd=cwd)


def spawn_new_console_series(command: list[str], *, cwd: str | None = None) -> int:
    return _new_console_process(command, cwd=cwd).wait()


def quote_cmd_arg(arg: str) -> str:
    if not arg:
        return '""'
    if not any(ch in arg for ch in ' \t&|()<>^"%!'):
        return arg
    return f'"{arg.replace(chr(34), chr(34) * 2)}"'


def join_cmd_args(args: list[str]) -> str:
    return " ".join(quote_cmd_arg(a) for a in args)


def echo_cmd_text(text: str) -> str:
    escaped = (
        text.replace("^", "^^")
        .replace("%", "%%")
        .replace("&", "^&")
        .replace("|", "^|")
        .replace("<", "^<")
        .replace(">", "^>")
        .replace('"', "'")
    )
    return f"echo {escaped}"
