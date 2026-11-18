from __future__ import annotations

from pathlib import Path

import jardiscordengine as JDE

from jarbot_modulable.commands.commands import register_commands
from jarbot_modulable.commands.terminal_commands import register_terminal_commands
from jarbot_modulable.constants import BOT_NAME
from jarbot_modulable.services.funny_helpers import get_funny
from jarbot_modulable.services.generic_helpers import log_info, move_logs
from jarbot_modulable.services.pterodactyl_helpers import request_pterodactyl_stop


def init(project_path: Path) -> None:
    get_funny(project_path)


async def main() -> None:
    log_info(
        "Bot setup",
        f"Setting up {BOT_NAME}.",
    )

    intents = JDE.Entities.JDEEntityIntents.default()

    intents.moderation = True

    bot = JDE.Bots.JDEBot(
        intents=intents,
        activity=JDE.Entities.JDEEntityActivityGame("Bot starting | o.O"),
        status=JDE.Entities.JDEStatus.IDLE,
        no_sync=("MESSAGES",),
    )

    log_info(
        "Bot setup",
        f"{BOT_NAME} ready.",
    )

    log_info(
        "Terminal setup",
        f"Setting up {BOT_NAME}.",
    )

    async def on_starting() -> None:
        log_info(
            "EVENT",
            "On starting ran",
        )

    async def on_started() -> None:
        await bot.sync_commands()
        await bot.change_presence(
            activity=JDE.Entities.JDEEntityActivityGame("Bot online | :D"),
            status=JDE.Entities.JDEStatus.ONLINE,
        )

        log_info(
            "EVENT",
            "On started ran",
        )

    async def on_closing() -> None:
        await bot.change_presence(
            activity=JDE.Entities.JDEEntityActivityGame("Bot offline | zzz"),
            status=JDE.Entities.JDEStatus.OFFLINE,
        )

        log_info(
            "EVENT",
            "On closing ran",
        )

    async def on_closed() -> None:
        log_info(
            "EVENT",
            "On closed ran",
        )

    terminal = JDE.Terminals.JDETerminal(bot, on_starting=on_starting, on_started=on_started, on_closing=on_closing, on_closed=on_closed)

    register_commands(bot)
    register_terminal_commands(terminal)

    log_info(
        "Terminal setup",
        f"{BOT_NAME} ready.",
    )

    log_info(
        "Bot startup",
        f"Starting {BOT_NAME}.",
    )

    await terminal.run()


if __name__ == "__main__":
    project_path = Path(__file__).resolve().parents[1]
    log_directory = project_path / "logs"
    jde_log_directory = project_path / ".jde-log"

    JDE.init(str(project_path))

    try:
        init(project_path)
        JDE.run(main)

    finally:
        JDE.quit()

        try:
            move_logs(jde_log_directory, log_directory)

        finally:
            request_pterodactyl_stop()
