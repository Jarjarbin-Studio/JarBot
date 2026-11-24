import jardiscordengine as JDE

from jarbot_modulable.constants import LIST_MESSAGE_LIMIT
from jarbot_modulable.services.terminal_commands.list import list_users, list_guilds, list_categories, list_channels, list_roles, list_messages
from jarbot_modulable.services.terminal_commands.announce import announce_members

BOT: JDE.Bots.JDEBot | None = None
TERMINAL: JDE.Terminals.JDETerminal | None = None


@JDE.Terminals.terminal_command(
    "list",
    "List all users synced in JarBot",
    ("type", "'users', 'guilds', 'categories', 'channels', 'roles', 'messages'")
)
async def list(args: list[str]):
    Console = JDE.Interns.Externs.JTKExternConsole

    if len(args) != 1:
        Console.print(Console.Text("Missing list type").f_color_error())
        return

    if args[0] == "users":
        await list_users(BOT)

    elif args[0] == "guilds":
        await list_guilds(BOT)

    elif args[0] == "categories":
        await list_categories(BOT)

    elif args[0] == "channels":
        await list_channels(BOT)

    elif args[0] == "roles":
        await list_roles(BOT)

    elif args[0] == "messages":
        await list_messages(BOT, LIST_MESSAGE_LIMIT)

    else:
        Console.print(
            Console.Text("Invalid list type ").f_color_error()
            + Console.Text(f"'{args[0]}'").f_style_bold().f_color_foreground(
                Console.ColorRGB(255, 190, 90)
            )
            + Console.Text(".").f_color_error()
        )

        Console.print(
            Console.Text("Available types: ").f_color_warning()
            + Console.Text("'users', 'guilds', 'categories', 'channels', 'roles', 'messages'").f_style_bold().f_color_success()
        )


@JDE.Terminals.terminal_command(
    "announce",
    "Send an important announcement to members through DMs",
)
async def announce(args: list[str]) -> None:
    Console = JDE.Interns.Externs.JTKExternConsole

    if args:
        Console.print(
            Console.Text("This command does not accept arguments.").f_color_error()
        )
        return

    if BOT is None:
        Console.print(
            Console.Text("The bot is not initialized.").f_color_error()
        )
        return

    await announce_members(BOT)


def register_terminal_commands(
        terminal: JDE.Terminals.JDETerminal
    ) -> None:
    global BOT, TERMINAL

    TERMINAL = terminal
    BOT = terminal.bot

    terminal.register_commands(
        list,
        announce,
    )
