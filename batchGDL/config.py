import json
import os
import shlex

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
BATCHGDL_CONFIG_PATH = os.path.normpath(os.path.join(_PACKAGE_DIR, "../batchGDL-config.json"))
_CONFIG_DIR = os.path.dirname(BATCHGDL_CONFIG_PATH)

config: dict = {}


def reload_config() -> None:
    with open(BATCHGDL_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    config.clear()
    config.update(data)


def save_config() -> None:
    with open(BATCHGDL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def config_file_path() -> str:
    path = str(config["config_file"])
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(_CONFIG_DIR, path))


def oauth_sites() -> list[str]:
    return [site for site in config.get("oauth-sites", []) if site]


def oauth_option_labels() -> list[str]:
    return ["All Sites", *oauth_sites()]


def single_list_option_labels() -> list[str]:
    return list(config.get("single-lists", {}))


def subscription_option_labels(download_all_label: str) -> list[str]:
    return [*config.get("subscriptions", {}), download_all_label]

def date_range_filter() -> str | None:
    raw = str(config.get("daterange", "")).strip()
    if not raw or raw == "YYYY, MM, DD":
        return None
    return f"date >= datetime({raw}) or abort()"

def entry_extra_flags(entry: list, index: int) -> str:
    if len(entry) <= index:
        return ""
    value = entry[index]
    return value.strip() if isinstance(value, str) else ""


def parse_extra_flags(flags: str | None) -> list[str]:
    if not flags or not str(flags).strip():
        return []
    try:
        return shlex.split(str(flags), posix=True)
    except ValueError:
        return str(flags).split()


def with_optional_flags(base: list[str], flags: str) -> list[str]:
    flags = flags.strip()
    if not flags:
        return base
    return [*base, flags]


reload_config()
