import os
import sys
import tempfile
from datetime import datetime

from .config import config, config_file_path, date_range_filter, entry_extra_flags, parse_extra_flags
from .constants import SUBSCRIPTION_LISTS_DIR
from .lists import lists_txt_path
from .system import echo_cmd_text, join_cmd_args


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


def log_download_job_cmd(job_name: str) -> str:
    path = os.path.abspath(log_file_path())
    py = (
        "from datetime import datetime;"
        f"p={path!r};"
        f"n={job_name!r};"
        "open(p,'a',encoding='utf-8').write("
        "'\\n-----[Download job '+chr(34)+n+chr(34)+' at '+"
        "datetime.now().isoformat(sep=' ',timespec='seconds')"
        "+']-----\\n')"
    )
    return join_cmd_args([sys.executable, "-c", py])


def build_command(
    *,
    dest_folder: str,
    input_file: str,
    path_key: str,
    archive: str | None = None,
    range_filter: str | None = None,
    lists_dir: str = SUBSCRIPTION_LISTS_DIR,
    extra_flags: str | None = None,
) -> list[str]:
    command = [
        "gallery-dl",
        "--config",
        config_file_path(),
        "--cookies-from-browser",
        config["cookies_browser"],
        "--destination",
        f"{config['dl_folder']}/{path_key}_dl/{dest_folder}/",
        "--input-file",
        lists_txt_path(input_file, lists_dir),
    ]
    if archive:
        command.extend(["--download-archive", f"archive/{archive}.sqlite3"])
    if range_filter:
        command.extend(["--filter", range_filter])
    command.extend(parse_extra_flags(extra_flags))
    return command


def build_download_all_script(subs: dict[str, list], *, work_dir: str | None = None) -> str:
    work_dir = os.path.abspath(work_dir or os.getcwd())
    rng = date_range_filter()
    jobs = [(name, tup) for name, tup in subs.items() if len(tup) >= 3]
    lines = [
        "@echo off",
        "setlocal",
        f'cd /d "{work_dir}"',
        "if errorlevel 1 (",
        echo_cmd_text(f"Failed to cd to {work_dir}"),
        "pause",
        "exit /b 1",
        ")",
        echo_cmd_text(f"Download All: {len(jobs)} subscription(s)"),
        "echo.",
    ]
    for index, (sub_name, tup) in enumerate(jobs, start=1):
        dest_folder, list_file, archive = tup[0], tup[1], tup[2]
        extra_flags = entry_extra_flags(tup, 3)
        command = build_command(
            dest_folder=dest_folder,
            input_file=list_file,
            path_key="sub",
            archive=archive,
            range_filter=rng,
            lists_dir=SUBSCRIPTION_LISTS_DIR,
            extra_flags=extra_flags,
        )
        lines.append(echo_cmd_text(f"[{index}/{len(jobs)}] {sub_name}"))
        lines.append(log_download_job_cmd(sub_name))
        lines.append(join_cmd_args(command))
        lines.append("if errorlevel 1 echo Job failed, continuing...")
        lines.append("echo.")
    lines.extend(
        [
            echo_cmd_text(f"Download All finished ({len(jobs)} subscription(s))."),
            "pause",
        ]
    )
    return "\n".join(lines)


def write_download_all_script(subs: dict[str, list], *, work_dir: str | None = None) -> str:
    fd, path = tempfile.mkstemp(prefix="batchGDL_download_all_", suffix=".cmd")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(build_download_all_script(subs, work_dir=work_dir))
    return path
