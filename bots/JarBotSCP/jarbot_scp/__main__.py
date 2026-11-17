from __future__ import annotations

from pathlib import Path

import jardiscordengine as JDE

from jarbot_scp.commands.commands import register_commands
from jarbot_scp.commands.terminal_commands import register_terminal_commands
from jarbot_scp.constants import BOT_NAME
from jarbot_scp.services.generic_helpers import log_error, log_info, move_logs


async def main() -> None:
    log_info(
        "Bot setup",
        f"Setting up {BOT_NAME}.",
    )

    bot = JDE.Bots.JDEBot(
        activity=JDE.Entities.JDEEntityActivityGame("Bot starting..."),
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

    async def on_ready() -> None:
        await bot.sync_commands()

        log_info(
            "EVENT",
            "On ready ran",
        )

    async def on_close() -> None:
        log_info(
            "EVENT",
            "On close ran",
        )

    terminal = JDE.Terminals.JDETerminal(bot, on_ready=on_ready, on_close=on_close)

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
        JDE.run(main)

    finally:
        JDE.quit()
        move_logs(jde_log_directory, log_directory)
