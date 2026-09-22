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


def pause() -> None:
    try:
        input("Press Enter to close...")
    except (EOFError, KeyboardInterrupt):
        pass


def _ensure_work_dir(work_dir: str) -> None:
    try:
        os.chdir(work_dir)
    except OSError:
        print(f"Failed to cd to {work_dir}")
        raise SystemExit(1)


def _build_python_launch_command(*, prefix: str, import_fn: str, call_expr: str) -> list[str]:
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=".py")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            "import sys\n"
            f"sys.path.insert(0, {package_root!r})\n"
            f"from batchGDL.downloads import pause, {import_fn}\n"
            "try:\n"
            f"    {call_expr}\n"
            "except KeyboardInterrupt:\n"
            '    print("\\nInterrupted by user.")\n'
            "finally:\n"
            "    pause()\n"
        )
    return [sys.executable, path]


def run_gallery_dl(command: list[str], work_dir: str) -> None:
    _ensure_work_dir(work_dir)
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"Download exited with code {result.returncode}.")


def build_download_job_command(command: list[str], *, work_dir: str | None = None) -> list[str]:
    work_dir = os.path.abspath(work_dir or os.getcwd())
    return _build_python_launch_command(
        prefix="batchGDL_download_job_",
        import_fn="run_gallery_dl",
        call_expr=f"run_gallery_dl({command!r}, {work_dir!r})",
    )


def run_download_all(jobs: list[tuple[str, list[str]]], work_dir: str) -> None:
    reload_config()
    _ensure_work_dir(work_dir)

    print(f"Download All: {len(jobs)} subscription(s)")
    print()
    try:
        for index, (name, command) in enumerate(jobs, start=1):
            print(f"[{index}/{len(jobs)}] {name}")
            try:
                log_download_job(name)
            except OSError as e:
                print(f"Could not write log header: {e}")
            try:
                result = subprocess.run(command)
            except KeyboardInterrupt:
                print("\nInterrupted by user.")
                break
            if result.returncode != 0:
                print("Job failed, continuing...")
            print()
        else:
            print(f"Finished downloading ({len(jobs)} subscription(s)).")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")


def build_download_all_command(subs: dict[str, list], *, work_dir: str | None = None) -> list[str]:
    work_dir = os.path.abspath(work_dir or os.getcwd())
    jobs = _download_all_jobs(subs)
    return _build_python_launch_command(
        prefix="batchGDL_download_all_",
        import_fn="run_download_all",
        call_expr=f"run_download_all({jobs!r}, {work_dir!r})",
    )
