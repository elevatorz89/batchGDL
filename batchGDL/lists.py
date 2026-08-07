import os
import re

from .constants import SUBSCRIPTION_LISTS_DIR


def slug_list_name(name: str) -> str:
    slug = re.sub(r"[^\w\-]", "", name.strip().lower().replace(" ", "_"))
    return slug or "list"


def lists_txt_path(name: str, lists_dir: str = SUBSCRIPTION_LISTS_DIR) -> str:
    return os.path.join(lists_dir, f"{name}.txt")


def ensure_list_txt(list_file: str, lists_dir: str = SUBSCRIPTION_LISTS_DIR) -> None:
    os.makedirs(lists_dir, exist_ok=True)
    txt_path = lists_txt_path(list_file, lists_dir)
    if not os.path.isfile(txt_path):
        with open(os.path.abspath(txt_path), "w", encoding="utf-8"):
            pass


def list_file_is_empty(list_file: str, lists_dir: str = SUBSCRIPTION_LISTS_DIR) -> bool:
    path = lists_txt_path(list_file, lists_dir)
    if not os.path.isfile(path):
        return True
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.strip():
                return False
    return True


def ensure_or_rename_list_txt(old_name: str | None, new_name: str, lists_dir: str) -> None:
    new_path = lists_txt_path(new_name, lists_dir)
    if old_name and old_name != new_name:
        old_path = lists_txt_path(old_name, lists_dir)
        if os.path.isfile(old_path) and not os.path.isfile(new_path):
            os.makedirs(lists_dir, exist_ok=True)
            os.rename(old_path, new_path)
            return
    ensure_list_txt(new_name, lists_dir)
