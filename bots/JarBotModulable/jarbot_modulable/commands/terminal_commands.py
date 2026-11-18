import jardiscordengine as JDE


BOT: JDE.Bots.JDEBot | None = None
TERMINAL: JDE.Terminals.JDETerminal | None = None


@JDE.Terminals.terminal_command(
    "list-users",
    "List all users synced in JarBot",
)
async def list_users(args: list[str]):
    JDE.Interns.Externs.JTKExternConsole.print("JarBot users synced in JarBot")


def register_terminal_commands(
        terminal: JDE.Terminals.JDETerminal
    ) -> None:
    global BOT, TERMINAL

    TERMINAL = terminal
    BOT = terminal.bot

    terminal.register_commands(
        list_users,
    )
