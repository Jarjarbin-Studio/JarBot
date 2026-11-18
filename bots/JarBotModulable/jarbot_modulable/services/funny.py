from pathlib import Path
from random import choice
from typing import Sequence

from jarbot_modulable.services.generic import log_info


BOT_FUNNY: Sequence[str] = []


def get_funny(
        project_path: Path | None = None
    ) -> str:
    global BOT_FUNNY

    if not BOT_FUNNY:
        if project_path is not None:
            with open(project_path / "assets" / "funny.txt", 'r') as funny_file:
                BOT_FUNNY = funny_file.readlines()

            log_info("File", f"Funny file has been loaded ({len(BOT_FUNNY)} quotes)")
        else:
            BOT_FUNNY = ["Funny not loaded..."]

    return choice(BOT_FUNNY)
