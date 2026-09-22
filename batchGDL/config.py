import json
import os
import shlex
import shutil
from time import sleep

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

def update_config(curr_version, new_version) -> None:
    backup_path = f"{BATCHGDL_CONFIG_PATH}.v{curr_version}.bak"
    shutil.copy(BATCHGDL_CONFIG_PATH, backup_path)
    print(f"Config backup copied to {backup_path}")

    with open(BATCHGDL_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    while curr_version < new_version:
        if curr_version == 0:
            print ("v1 Config Detected.")
            curr_version = 1
        if curr_version == 1:
            tmp = data["single-lists"]
            tmp2 = data["subscriptions"]
            tmp3 = data["daterange"]
            tmp4 = data["cookies_browser"]

            data["download-jobs"] = {}
            data["download-jobs"]["single"] = tmp
            data["download-jobs"]["subscription"] = tmp2
            data["global-flags-single"] = [f"--cookies-from-browser {tmp4}"]
            data["global-flags-subscriptions"] = [f"--filter 'date >= datetime({tmp3}) or abort()' --cookies-from-browser {tmp4}"]

            data.pop("single-lists")
            data.pop("subscriptions")
            data.pop("daterange")
            data.pop("cookies_browser")
            data.pop("#", None)

            data["config_ver"] = 2
            print("Config updated to v2.")
            curr_version = 2

    with open(BATCHGDL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    config.clear()
    config.update(data)
    sleep(3)


    #config[key] = value
    #save_config()


def config_file_path() -> str:
    path = str(config["config_file"])
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(_CONFIG_DIR, path))


def oauth_sites() -> list[str]:
    return [site for site in config.get("oauth-sites", []) if site]


def oauth_option_labels() -> list[str]:
    return ["All Sites", *oauth_sites()]


def job_section(kind: str) -> dict:
    return config.setdefault("download-jobs", {}).setdefault(kind, {})


def single_list_option_labels() -> list[str]:
    return list(job_section("single"))


def subscription_option_labels(download_all_label: str) -> list[str]:
    return [*job_section("subscription"), download_all_label]


def global_flags_string(config_key: str) -> str:
    flags = config.get(config_key) or []
    if isinstance(flags, str):
        return flags.strip()
    return " ".join(str(flag).strip() for flag in flags if str(flag).strip())

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
    flags = flags.strip().replace('"', "'")
    if not flags:
        return base
    return [*base, flags]


reload_config()
