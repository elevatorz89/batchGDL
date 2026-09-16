import json
import shutil
import importlib.util

from . import config as _cfg_module
from .config import BATCHGDL_CONFIG_PATH
from constants import CONFIG_VERSION


def check_dependencies() -> list[str]:
    missing: list[str] = []
    if not shutil.which("gallery-dl"):
        missing.append("gallery-dl")
    for package in ("textual", "rapidfuzz"):
        if importlib.util.find_spec(package) is None:
            missing.append(package)
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
    return missing


def check_setup() -> bool:
    with open(BATCHGDL_CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "setup" not in data:
        data["setup"] = "false"
        with open(BATCHGDL_CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        _cfg_module.config.clear()
        _cfg_module.config.update(data)
        return False
    if data.get("setup") == "false":
        return False
    return True


def mark_setup_complete() -> None:
    with open(BATCHGDL_CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    data["setup"] = "true"
    _cfg_module.config.clear()
    _cfg_module.config.update(data)

def get_config_version() -> None:
    with open(BATCHGDL_CONFIG_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "config_ver" not in data:
        print(f"Updating config...")
        _cfg_module.update_config(0, CONFIG_VERSION)
    elif data["config_ver"] < CONFIG_VERSION:
        print(f"Updating config...")
        _cfg_module.update_config(data["config_ver"], CONFIG_VERSION)

#    return data.get("config_ver", 0) == _cfg_module.CONFIG_VERSION