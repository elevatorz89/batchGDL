import json
import shutil
import importlib.util
import tempfile
import os

from . import config as _cfg_module
from .config import BATCHGDL_CONFIG_PATH
from .constants import CONFIG_VERSION

# checks if all python packages are installed
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

# checks if setup exists and/or is complete
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

# sets setup key to true
def mark_setup_complete() -> None:
    _cfg_module.config["setup"] = "true"
    _cfg_module.save_config()

# checks config version and migrates if necessary
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

# cleans up pycache files
def clear_download_temp_scripts() -> None:
    temp_dir = tempfile.gettempdir()
    for name in os.listdir(temp_dir):
        if not (name.startswith("batchGDL_download_") and name.endswith(".py")):
            continue
        path = os.path.join(temp_dir, name)
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass