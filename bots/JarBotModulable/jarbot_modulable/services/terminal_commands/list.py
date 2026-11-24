
import discord
import jardiscordengine as JDE


def _get_console():
    return JDE.Interns.Externs.JTKExternConsole


def _guild_header(Console, guild):
    return (
        Console.Text("Guild ").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
        + Console.Text(f"'{guild.name}'").f_style_bold().f_color_foreground(
            Console.ColorRGB(100, 180, 255)
        )
        + Console.Text(" [").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
        + Console.Text(str(guild.id)).f_color_foreground(
            Console.ColorRGB(180, 180, 180)
        )
        + Console.Text("]:\n").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
    )


def _tree(Console, text, color=None, bold=False):
    result = Console.Text(text)

    if bold:
        result = result.f_style_bold()

    if color is not None:
        result = result.f_color_foreground(color)

    return result


def _check_bot(bot, Console):
    if not bot.synchronized:
        Console.print(
            Console.Text("The bot is not synchronized...").f_color_error()
            + "\n\n"
        )
        return False

    return True


# =============================================================================
# Users
# =============================================================================

async def list_users(bot: JDE.Bots.JDEBot):
    Console = _get_console()

    if not _check_bot(bot, Console):
        return

    output = Console.Text()

    for guild in bot.guilds.items():
        discord_guild = bot.discord.get_guild(guild[0])

        output += _guild_header(Console, guild[1])

        if discord_guild is None:
            output += (
                _tree(
                    Console,
                    "  └─ Unable to retrieve guild",
                    Console.ColorRGB(255, 100, 100)
                )
                + "\n\n"
            )
            continue

        members = []

        try:
            async for member in discord_guild.fetch_members(limit=None):
                members.append(member)

        except discord.Forbidden:
            output += (
                _tree(
                    Console,
                    "  └─ Missing permissions to retrieve members",
                    Console.ColorRGB(255, 100, 100)
                )
                + "\n\n"
            )
            continue

        except discord.HTTPException as error:
            output += (
                _tree(
                    Console,
                    "  └─ Unable to retrieve members: ",
                    Console.ColorRGB(255, 100, 100)
                )
                + _tree(
                    Console,
                    str(error),
                    Console.ColorRGB(255, 170, 100)
                )
                + "\n\n"
            )
            continue

        if not members:
            output += (
                _tree(
                    Console,
                    "  └─ No members",
                    Console.ColorRGB(150, 150, 150)
                )
                + "\n\n"
            )
            continue

        for index, member in enumerate(members):
            is_last = index == len(members) - 1
            is_bot = (
                bot.discord.user is not None
                and member.id == bot.discord.user.id
            )

            prefix = "  └─ " if is_last else "  ├─ "

            display_color = (
                Console.ColorRGB(100, 220, 150)
                if is_bot
                else Console.ColorRGB(230, 230, 230)
            )

            output += (
                _tree(
                    Console,
                    prefix,
                    Console.ColorRGB(100, 100, 100)
                )
                + _tree(
                    Console,
                    member.display_name,
                    display_color,
                    bold=True
                )
                + _tree(
                    Console,
                    " <Current Bot>" if is_bot else f" ({member.name})",
                    Console.ColorRGB(150, 150, 150)
                ).f_style_italic()
                + (
                    _tree(
                        Console,
                        f" [{member.id}]",
                        Console.ColorRGB(100, 160, 220)
                    )
                    if not is_bot
                    else Console.Text("")
                )
                + "\n"
            )

        output += "\n"

    Console.print(output)


# =============================================================================
# Guilds
# =============================================================================

async def list_guilds(bot: JDE.Bots.JDEBot):
    Console = _get_console()

    if not _check_bot(bot, Console):
        return

    output = Console.Text()

    for index, guild in enumerate(bot.guilds.items()):
        output += (
            _guild_header(Console, guild[1])
            + _tree(
                Console,
                "  └─ Connected",
                Console.ColorRGB(100, 220, 150)
            )
            + "\n\n"
        )

    Console.print(output)


# =============================================================================
# Categories
# =============================================================================

async def list_categories(bot: JDE.Bots.JDEBot):
    Console = _get_console()

    if not _check_bot(bot, Console):
        return

    output = Console.Text()

    for guild in bot.guilds.items():
        discord_guild = bot.discord.get_guild(guild[0])

        output += _guild_header(Console, guild[1])

        if discord_guild is None:
            output += (
                _tree(
                    Console,
                    "  └─ Unable to retrieve guild",
                    Console.ColorRGB(255, 100, 100)
                )
                + "\n\n"
            )
            continue

        categories = discord_guild.categories

        if not categories:
            output += (
                _tree(
                    Console,
                    "  └─ No categories",
                    Console.ColorRGB(150, 150, 150)
                )
                + "\n\n"
            )
            continue

        for index, category in enumerate(categories):
            is_last = index == len(categories) - 1
            prefix = "  └─ " if is_last else "  ├─ "

            output += (
                _tree(Console, prefix, Console.ColorRGB(100, 100, 100))
                + _tree(
                    Console,
                    category.name,
                    Console.ColorRGB(190, 150, 255),
                    bold=True
                )
                + _tree(
                    Console,
                    f" [{category.id}]",
                    Console.ColorRGB(150, 150, 150)
                )
                + "\n"
            )

    Console.print(output)


# =============================================================================
# Channels
# =============================================================================

async def list_channels(bot: JDE.Bots.JDEBot):
    Console = _get_console()

    if not _check_bot(bot, Console):
        return

    output = Console.Text()

    for guild in bot.guilds.items():
        discord_guild = bot.discord.get_guild(guild[0])

        output += _guild_header(Console, guild[1])

        if discord_guild is None:
            output += (
                _tree(
                    Console,
                    "  └─ Unable to retrieve guild",
                    Console.ColorRGB(255, 100, 100)
                )
                + "\n\n"
            )
            continue

        categories = discord_guild.categories
        uncategorized = [
            channel
            for channel in discord_guild.channels
            if not isinstance(channel, discord.CategoryChannel)
            and channel.category is None
        ]

        if not categories and not uncategorized:
            output += (
                _tree(
                    Console,
                    "  └─ No channels",
                    Console.ColorRGB(150, 150, 150)
                )
                + "\n\n"
            )
            continue

        for category_index, category in enumerate(categories):
            category_channels = category.channels

            output += (
                _tree(
                    Console,
                    "  ├─ Category: ",
                    Console.ColorRGB(100, 100, 100)
                )
                + _tree(
                    Console,
                    category.name,
                    Console.ColorRGB(190, 150, 255),
                    bold=True
                )
                + "\n"
            )

            if not category_channels:
                output += (
                    _tree(
                        Console,
                        "  │  └─ Empty",
                        Console.ColorRGB(150, 150, 150)
                    )
                    + "\n"
                )
                continue

            for channel_index, channel in enumerate(category_channels):
                is_last = channel_index == len(category_channels) - 1
                prefix = "  │  └─ " if is_last else "  │  ├─ "

                output += (
                    _tree(
                        Console,
                        prefix,
                        Console.ColorRGB(100, 100, 100)
                    )
                    + _tree(
                        Console,
                        f"#{channel.name}",
                        Console.ColorRGB(100, 200, 255),
                        bold=True
                    )
                    + _tree(
                        Console,
                        f" ({channel.type})",
                        Console.ColorRGB(150, 150, 150)
                    )
                    + _tree(
                        Console,
                        f" [{channel.id}]",
                        Console.ColorRGB(100, 160, 220)
                    )
                    + "\n"
                )

        if uncategorized:
            output += (
                _tree(
                    Console,
                    "  └─ Uncategorized channels",
                    Console.ColorRGB(150, 150, 150),
                    bold=True
                )
                + "\n"
            )

            for index, channel in enumerate(uncategorized):
                is_last = index == len(uncategorized) - 1
                prefix = "     └─ " if is_last else "     ├─ "

                output += (
                    _tree(
                        Console,
                        prefix,
                        Console.ColorRGB(100, 100, 100)
                    )
                    + _tree(
                        Console,
                        f"#{channel.name}",
                        Console.ColorRGB(100, 200, 255),
                        bold=True
                    )
                    + _tree(
                        Console,
                        f" ({channel.type})",
                        Console.ColorRGB(150, 150, 150)
                    )
                    + _tree(
                        Console,
                        f" [{channel.id}]",
                        Console.ColorRGB(100, 160, 220)
                    )
                    + "\n"
                )

        output += "\n"

    Console.print(output)


# =============================================================================
# Roles
# =============================================================================

async def list_roles(bot: JDE.Bots.JDEBot):
    Console = _get_console()

    if not _check_bot(bot, Console):
        return

    output = Console.Text()

    for guild in bot.guilds.items():
        discord_guild = bot.discord.get_guild(guild[0])

        output += _guild_header(Console, guild[1])

        if discord_guild is None:
            output += (
                _tree(
                    Console,
                    "  └─ Unable to retrieve guild",
                    Console.ColorRGB(255, 100, 100)
                )
                + "\n\n"
            )
            continue

        roles = sorted(
            discord_guild.roles,
            key=lambda role: role.position,
            reverse=True
        )

        for index, role in enumerate(roles):
            is_last = index == len(roles) - 1
            prefix = "  └─ " if is_last else "  ├─ "

            role_color = (
                Console.ColorRGB(
                    role.color.r,
                    role.color.g,
                    role.color.b
                )
                if role.color.value
                else Console.ColorRGB(190, 190, 190)
            )

            output += (
                _tree(
                    Console,
                    prefix,
                    Console.ColorRGB(100, 100, 100)
                )
                + _tree(
                    Console,
                    role.name,
                    role_color,
                    bold=True
                )
                + _tree(
                    Console,
                    f" (Position: {role.position})",
                    Console.ColorRGB(150, 150, 150)
                )
                + _tree(
                    Console,
                    f" [{role.id}]",
                    Console.ColorRGB(100, 160, 220)
                )
                + "\n"
            )

    Console.print(output)


# =============================================================================
# Latest Messages
# =============================================================================

async def list_messages(
        bot: JDE.Bots.JDEBot,
        limit: int = 10
    ):
    Console = _get_console()

    if not _check_bot(bot, Console):
        return

    output = Console.Text()
    messages = []

    for guild in bot.guilds.items():
        discord_guild = bot.discord.get_guild(guild[0])

        if discord_guild is None:
            continue

        for channel in discord_guild.text_channels:
            try:
                async for message in channel.history(limit=limit):
                    messages.append((
                        message.created_at,
                        message,
                        discord_guild
                    ))

            except discord.Forbidden:
                continue

            except discord.HTTPException:
                continue

    messages.sort(
        key=lambda item: item[0],
        reverse=True
    )

    messages = messages[:limit]

    output += (
        Console.Text("Latest ")
        + Console.Text(str(len(messages))).f_style_bold().f_color_foreground(
            Console.ColorRGB(100, 200, 255)
        )
        + Console.Text(" messages:\n\n")
    )

    if not messages:
        output += _tree(
            Console,
            "No messages available.",
            Console.ColorRGB(150, 150, 150)
        )
        Console.print(output)
        return

    for index, (timestamp, message, guild) in enumerate(messages):
        is_last = index == len(messages) - 1
        prefix = "└─ " if is_last else "├─ "

        is_bot = (
            bot.discord.user is not None
            and message.author.id == bot.discord.user.id
        )

        author_color = (
            Console.ColorRGB(100, 220, 150)
            if is_bot
            else Console.ColorRGB(230, 230, 230)
        )

        content = message.content.strip()

        if not content:
            if message.attachments:
                content = "[Attachment]"
            elif message.embeds:
                content = "[Embed]"
            else:
                content = "[Empty message]"

        if len(content) > 120:
            content = content[:117] + "..."

        output += (
            _tree(
                Console,
                prefix,
                Console.ColorRGB(100, 100, 100)
            )
            + Console.Text(
                message.author.display_name
            ).f_style_bold().f_color_foreground(author_color)
            + Console.Text(
                " <Bot>" if is_bot else ""
            ).f_style_italic().f_color_foreground(
                Console.ColorRGB(100, 220, 150)
            )
            + "\n"
            + _tree(
                Console,
                f"   {guild.name} / ",
                Console.ColorRGB(150, 150, 150)
            )
            + _tree(
                Console,
                f"#{message.channel.name}",
                Console.ColorRGB(100, 180, 255)
            )
            + "\n"
            + _tree(
                Console,
                f"   {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                Console.ColorRGB(150, 150, 150)
            )
            + "\n"
            + _tree(
                Console,
                f"   {content}",
                Console.ColorRGB(210, 210, 210)
            )
            + "\n\n"
        )

    Console.print(output)
