import shutil
from pathlib import Path

import jardiscordengine as JDE


def log_info(title: str, description: str) -> None:
    JDE.Interns.Logs.log("INFO", title, description)

def log_warning(title: str, description: str) -> None:
    JDE.Interns.Logs.log("WARN", title, description)

def log_error(title: str, description: str) -> None:
    JDE.Interns.Logs.log("ERROR", title, description)

def move_logs(jde_log_directory: Path, log_directory: Path):
    log_directory.mkdir(parents=True, exist_ok=True)

    if jde_log_directory.is_dir():
        for log_file in jde_log_directory.glob("*.jar-log"):
            shutil.move(
                str(log_file),
                str(log_directory / log_file.name),
            )
