import os
import subprocess
import sys
import tempfile
from datetime import datetime

from .config import (
    config,
    config_file_path,
    entry_extra_flags,
    global_flags_string,
    parse_extra_flags,
    reload_config,
)
from .constants import SUBSCRIPTION_LISTS_DIR
from .lists import lists_txt_path


def log_file_path() -> str:
    return config.get("log_file") or "logfile_latest.txt"


def log_download_job(job_name: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f'\n-----[Download job "{job_name}" at {stamp}]-----\n'
    path = log_file_path()
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(entry)


def build_command(
    *,
    dest_folder: str,
    input_file: str,
    path_key: str,
    archive: str | None = None,
    lists_dir: str = SUBSCRIPTION_LISTS_DIR,
    global_flags: str | None = None,
    extra_flags: str | None = None,
) -> list[str]:
    command = [
        "gallery-dl",
        "--config",
        config_file_path(),
        "--destination",
        f"{config['dl_folder']}/{path_key}_dl/{dest_folder}/",
        "--input-file",
        lists_txt_path(input_file, lists_dir),
    ]
    if archive:
        command.extend(["--download-archive", f"archive/{archive}.sqlite3"])
    command.extend(parse_extra_flags(global_flags))
    command.extend(parse_extra_flags(extra_flags))
    return command


def _download_all_jobs(subs: dict[str, list]) -> list[tuple[str, list[str]]]:
    global_flags = global_flags_string("global-flags-subscriptions")
    jobs: list[tuple[str, list[str]]] = []
    for name, tup in subs.items():
        if len(tup) < 3:
            continue
        dest_folder, list_file, archive = tup[0], tup[1], tup[2]
        jobs.append(
            (
                name,
                build_command(
                    dest_folder=dest_folder,
                    input_file=list_file,
                    path_key="sub",
                    archive=archive,
                    lists_dir=SUBSCRIPTION_LISTS_DIR,
                    global_flags=global_flags,
                    extra_flags=entry_extra_flags(tup, 3),
                ),
            )
        )
    return jobs


def _pause() -> None:
    try:
        input("Press Enter to close...")
    except EOFError:
        pass


def run_download_all(jobs: list[tuple[str, list[str]]], work_dir: str) -> None:
    reload_config()
    try:
        os.chdir(work_dir)
    except OSError:
        print(f"Failed to cd to {work_dir}")
        _pause()
        raise SystemExit(1)

    print(f"Download All: {len(jobs)} subscription(s)")
    print()
    for index, (name, command) in enumerate(jobs, start=1):
        print(f"[{index}/{len(jobs)}] {name}")
        try:
            log_download_job(name)
        except OSError as e:
            print(f"Could not write log header: {e}")
        if subprocess.run(command).returncode != 0:
            print("Job failed, continuing...")
        print()
    print(f"Download All finished ({len(jobs)} subscription(s)).")
    _pause()


def build_download_all_command(subs: dict[str, list], *, work_dir: str | None = None) -> list[str]:
    work_dir = os.path.abspath(work_dir or os.getcwd())
    jobs = _download_all_jobs(subs)
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fd, path = tempfile.mkstemp(prefix="batchGDL_download_all_", suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            "import sys\n"
            f"sys.path.insert(0, {package_root!r})\n"
            "from batchGDL.downloads import run_download_all\n"
            f"run_download_all({jobs!r}, {work_dir!r})\n"
        )
    return [sys.executable, path]
