import asyncio

import discord
import jardiscordengine as JDE


# =============================================================================
# Console helpers
# =============================================================================


def _get_console():
    return JDE.Interns.Externs.JTKExternConsole


def _tree(Console, text, color=None, bold=False):
    result = Console.Text(text)

    if bold:
        result = result.f_style_bold()

    if color is not None:
        result = result.f_color_foreground(color)

    return result


def _guild_header(Console, guild):
    return (
        Console.Text("Guild ").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
        + Console.Text(
            f"'{guild.name}'"
        ).f_style_bold().f_color_foreground(
            Console.ColorRGB(100, 180, 255)
        )
        + Console.Text(" [").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
        + Console.Text(
            str(guild.id)
        ).f_color_foreground(
            Console.ColorRGB(180, 180, 180)
        )
        + Console.Text("]:\n").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
    )


def _check_bot(bot, Console):
    if not bot.synchronized:
        Console.print(
            Console.Text(
                "The bot is not synchronized..."
            ).f_color_error()
            + "\n\n"
        )
        return False

    if bot.discord.user is None:
        Console.print(
            Console.Text(
                "The Discord bot is not connected."
            ).f_color_error()
            + "\n\n"
        )
        return False

    return True


async def _read_input(prompt: str = "") -> str:
    return JDE.Interns.Externs.JTKExternConsole.Console.Console.input(prompt=prompt)


def _print_error(message: str) -> None:
    Console = _get_console()

    Console.print(
        Console.Text(message).f_color_error()
    )


# =============================================================================
# Target retrieval
# =============================================================================


async def _fetch_guild_members(guild: discord.Guild) -> list[discord.Member]:
    members = []

    async for member in guild.fetch_members(limit=None):
        members.append(member)

    return members


async def _get_guild_targets(bot):
    """
    Return all available guilds.

    Each entry contains:
    - The guild object.
    - Its Discord guild object.
    """
    targets = []

    for guild_id, guild in bot.guilds.items():
        discord_guild = bot.discord.get_guild(guild_id)

        if discord_guild is None:
            continue

        targets.append({
            "guild": guild,
            "discord_guild": discord_guild,
        })

    return targets


async def _get_role_targets(bot):
    """
    Return all roles from all available guilds.
    """
    targets = []

    for guild_id, guild in bot.guilds.items():
        discord_guild = bot.discord.get_guild(guild_id)

        if discord_guild is None:
            continue

        roles = sorted(
            discord_guild.roles,
            key=lambda role: role.position,
            reverse=True,
        )

        for role in roles:
            targets.append({
                "guild": guild,
                "discord_guild": discord_guild,
                "role": role,
            })

    return targets


async def _get_user_targets(bot):
    """
    Retrieve members from all available guilds.

    Members are kept grouped by guild, matching the list users output.
    """
    targets = []

    for guild_id, guild in bot.guilds.items():
        discord_guild = bot.discord.get_guild(guild_id)

        if discord_guild is None:
            continue

        try:
            members = await _fetch_guild_members(discord_guild)

        except discord.Forbidden:
            continue

        except discord.HTTPException:
            continue

        for member in members:
            targets.append({
                "guild": guild,
                "discord_guild": discord_guild,
                "member": member,
            })

    return targets


# =============================================================================
# Target selection
# =============================================================================


def _display_guild_targets(targets) -> None:
    Console = _get_console()
    output = Console.Text()

    for index, target in enumerate(targets, start=1):
        guild = target["guild"]

        output += (
            _guild_header(Console, guild)
            + _tree(
                Console,
                f"  └─ [{index}] Connected",
                Console.ColorRGB(100, 220, 150),
            )
            + "\n\n"
        )

    Console.print(output)


def _display_role_targets(targets) -> None:
    Console = _get_console()
    output = Console.Text()

    current_guild_id = None

    for index, target in enumerate(targets, start=1):
        guild = target["guild"]
        role = target["role"]

        if guild.id != current_guild_id:
            output += _guild_header(Console, guild)
            current_guild_id = guild.id

        role_color = (
            Console.ColorRGB(
                role.color.r,
                role.color.g,
                role.color.b,
            )
            if role.color.value
            else Console.ColorRGB(190, 190, 190)
        )

        output += (
            _tree(
                Console,
                f"  └─ [{index}] ",
                Console.ColorRGB(100, 100, 100),
            )
            + _tree(
                Console,
                role.name,
                role_color,
                bold=True,
            )
            + _tree(
                Console,
                f" (Position: {role.position})",
                Console.ColorRGB(150, 150, 150),
            )
            + _tree(
                Console,
                f" [{role.id}]",
                Console.ColorRGB(100, 160, 220),
            )
            + "\n"
        )

    Console.print(output)


def _display_user_targets(targets) -> None:
    Console = _get_console()
    output = Console.Text()

    current_guild_id = None

    for index, target in enumerate(targets, start=1):
        guild = target["guild"]
        member = target["member"]

        if guild.id != current_guild_id:
            output += _guild_header(Console, guild)
            current_guild_id = guild.id

        is_bot = member.bot

        display_color = (
            Console.ColorRGB(100, 220, 150)
            if is_bot
            else Console.ColorRGB(230, 230, 230)
        )

        output += (
            _tree(
                Console,
                f"  └─ [{index}] ",
                Console.ColorRGB(100, 100, 100),
            )
            + _tree(
                Console,
                member.display_name,
                display_color,
                bold=True,
            )
            + _tree(
                Console,
                f" ({member.name})",
                Console.ColorRGB(150, 150, 150),
            ).f_style_italic()
            + _tree(
                Console,
                f" [{member.id}]",
                Console.ColorRGB(100, 160, 220),
            )
            + "\n"
        )

    Console.print(output)


async def _select_scope() -> str | None:
    Console = _get_console()

    choices = {
        "1": "guild",
        "2": "role",
        "3": "user",
    }

    Console.print(
        Console.Text("\nAnnouncement scope\n").f_style_bold()
        + _tree(Console, "  [1] Guild\n", Console.ColorRGB(100, 200, 255))
        + _tree(Console, "  [2] Role\n", Console.ColorRGB(190, 150, 255))
        + _tree(Console, "  [3] User\n", Console.ColorRGB(100, 220, 150))
        + _tree(Console, "\n  [Q] Cancel\n", Console.ColorRGB(255, 100, 100))
    )

    while True:
        answer = (await _read_input("Select scope: ")).strip().lower()

        if answer == "q":
            return None

        if answer in choices:
            return choices[answer]

        _print_error("Invalid choice. Enter 1, 2, 3 or Q.")


async def _select_target(targets, display_function, target_type: str):
    Console = _get_console()

    if not targets:
        _print_error(f"No available {target_type} were found.")
        return None

    display_function(targets)

    Console.print(
        Console.Text(
            f"\nSelect a {target_type} by its number."
        ).f_color_warning()
        + "\n"
        + _tree(
            Console,
            "Enter Q to cancel.\n",
            Console.ColorRGB(255, 100, 100),
        )
    )

    while True:
        answer = (await _read_input("Selection: ")).strip().lower()

        if answer == "q":
            return None

        if not answer.isdigit():
            _print_error("Please enter a valid number.")
            continue

        index = int(answer) - 1

        if 0 <= index < len(targets):
            return targets[index]

        _print_error(
            f"Invalid selection. Choose a number between 1 and {len(targets)}."
        )


# =============================================================================
# Message composition
# =============================================================================


async def _ask_title() -> str | None:
    Console = _get_console()

    while True:
        title = (await _read_input("\nAnnouncement title: ")).strip()

        if title.lower() == "q":
            return None

        if not title:
            _print_error("The title cannot be empty.")
            continue

        if len(title) > 256:
            _print_error("The title cannot exceed 256 characters.")
            continue

        return title


async def _ask_body() -> str | None:
    Console = _get_console()

    Console.print(
        Console.Text("\nAnnouncement body\n").f_style_bold()
        + _tree(
            Console,
            "Enter the message below.\n",
            Console.ColorRGB(150, 150, 150),
        )
        + _tree(
            Console,
            "Enter a single '.' on a line to finish.\n",
            Console.ColorRGB(150, 150, 150),
        )
        + _tree(
            Console,
            "Enter /cancel on a line to cancel.\n\n",
            Console.ColorRGB(255, 100, 100),
        )
    )

    lines = []

    while True:
        line = await _read_input()

        if line == ".":
            break

        if line.strip().lower() == "/cancel":
            return None

        lines.append(line)

        if len("\n".join(lines)) > 4096:
            _print_error(
                "The body cannot exceed 4096 characters. "
                "Please restart the body."
            )
            return None

    body = "\n".join(lines).strip()

    if not body:
        _print_error("The body cannot be empty.")
        return None

    return body


# =============================================================================
# Recipient resolution
# =============================================================================


async def _get_recipients(target_type: str, target) -> list[discord.Member]:
    """
    Resolve the selected target into a list of members.
    """
    if target_type == "guild":
        guild = target["discord_guild"]

        return await _fetch_guild_members(guild)

    if target_type == "role":
        guild = target["discord_guild"]
        role = target["role"]

        members = await _fetch_guild_members(guild)

        return [
            member
            for member in members
            if role in member.roles
        ]

    if target_type == "user":
        return [target["member"]]

    return []


def _unique_recipients(
        recipients: list[discord.Member],
        bot_user_id: int,
    ) -> list[discord.Member]:
    """
    Remove duplicate users and exclude bots.
    """
    unique = []
    seen = set()

    for member in recipients:
        if member.id == bot_user_id or member.bot:
            continue

        if member.id in seen:
            continue

        seen.add(member.id)
        unique.append(member)

    return unique


# =============================================================================
# Preview and confirmation
# =============================================================================


def _display_preview(
        title: str,
        body: str,
        recipient_count: int,
    ) -> None:
    Console = _get_console()

    output = (
        Console.Text("\nAnnouncement preview\n").f_style_bold()
        + _tree(
            Console,
            "─" * 50 + "\n",
            Console.ColorRGB(100, 100, 100),
        )
        + Console.Text(title).f_style_bold().f_color_foreground(
            Console.ColorRGB(100, 200, 255)
        )
        + "\n\n"
        + Console.Text(body).f_color_foreground(
            Console.ColorRGB(220, 220, 220)
        )
        + "\n\n"
        + _tree(
            Console,
            "─" * 50 + "\n",
            Console.ColorRGB(100, 100, 100),
        )
        + Console.Text("Recipients: ").f_color_warning()
        + Console.Text(
            str(recipient_count)
        ).f_style_bold().f_color_success()
        + "\n"
    )

    Console.print(output)


async def _confirm_announcement() -> bool:
    Console = _get_console()

    Console.print(
        Console.Text("\nConfirm announcement\n").f_style_bold()
        + _tree(
            Console,
            "  [Y] Send announcement\n",
            Console.ColorRGB(100, 220, 150),
        )
        + _tree(
            Console,
            "  [N] Cancel\n",
            Console.ColorRGB(255, 100, 100),
        )
    )

    while True:
        answer = (await _read_input("Confirmation: ")).strip().lower()

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no", "q"):
            return False

        _print_error("Enter Y or N.")


# =============================================================================
# Sending
# =============================================================================


async def _send_announcement(
        recipients: list[discord.Member],
        title: str,
        body: str,
) -> tuple[int, int]:
    """
    Send the announcement to each recipient sequentially.

    Returns:
        (successful_sends, failed_sends)
    """
    success = 0
    failed = 0

    embed = discord.Embed(
        title=title,
        description=body,
        color=discord.Color.blue(),
    )

    for index, member in enumerate(recipients, start=1):
        Console = _get_console()

        try:
            await member.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )

            success += 1

            Console.print(
                _tree(
                    Console,
                    f"[{index}/{len(recipients)}] ",
                    Console.ColorRGB(150, 150, 150),
                )
                + _tree(
                    Console,
                    member.display_name,
                    Console.ColorRGB(100, 220, 150),
                    bold=True,
                )
                + _tree(
                    Console,
                    " - Sent",
                    Console.ColorRGB(100, 220, 150),
                )
            )

        except discord.Forbidden:
            failed += 1

            Console.print(
                _tree(
                    Console,
                    f"[{index}/{len(recipients)}] ",
                    Console.ColorRGB(150, 150, 150),
                )
                + _tree(
                    Console,
                    member.display_name,
                    Console.ColorRGB(230, 230, 230),
                )
                + _tree(
                    Console,
                    " - DM unavailable",
                    Console.ColorRGB(255, 100, 100),
                )
            )

        except discord.HTTPException as error:
            failed += 1

            Console.print(
                _tree(
                    Console,
                    f"[{index}/{len(recipients)}] ",
                    Console.ColorRGB(150, 150, 150),
                )
                + _tree(
                    Console,
                    member.display_name,
                    Console.ColorRGB(230, 230, 230),
                )
                + _tree(
                    Console,
                    f" - HTTP error: {error}",
                    Console.ColorRGB(255, 100, 100),
                )
            )

    return success, failed


# =============================================================================
# Main workflow
# =============================================================================


async def announce_members(bot: JDE.Bots.JDEBot) -> None:
    Console = _get_console()

    if not _check_bot(bot, Console):
        return

    Console.print(
        Console.Text("\n")
        + Console.Text("Announcement wizard").f_style_bold().f_color_success()
        + "\n"
    )

    # -------------------------------------------------------------------------
    # 1. Scope
    # -------------------------------------------------------------------------

    target_type = await _select_scope()

    if target_type is None:
        Console.print(
            Console.Text("Announcement cancelled.").f_color_warning()
        )
        return

    # -------------------------------------------------------------------------
    # 2. Target
    # -------------------------------------------------------------------------

    if target_type == "guild":
        targets = await _get_guild_targets(bot)
        display_function = _display_guild_targets

    elif target_type == "role":
        targets = await _get_role_targets(bot)
        display_function = _display_role_targets

    else:
        Console.print(
            Console.Text(
                "\nRetrieving members from all guilds..."
            ).f_color_warning()
        )

        targets = await _get_user_targets(bot)
        display_function = _display_user_targets

    target = await _select_target(
        targets,
        display_function,
        target_type,
    )

    if target is None:
        Console.print(
            Console.Text("Announcement cancelled.").f_color_warning()
        )
        return

    # -------------------------------------------------------------------------
    # 3. Resolve recipients
    # -------------------------------------------------------------------------

    Console.print(
        Console.Text("\nRetrieving announcement recipients...")
        .f_color_warning()
    )

    try:
        recipients = await _get_recipients(target_type, target)

    except discord.Forbidden:
        _print_error(
            "Missing permissions to retrieve members from this guild."
        )
        return

    except discord.HTTPException as error:
        _print_error(
            f"Unable to retrieve members: {error}"
        )
        return

    recipients = _unique_recipients(
        recipients,
        bot.discord.user.id,
    )

    if not recipients:
        _print_error("No eligible recipients were found.")
        return

    # -------------------------------------------------------------------------
    # 4. Title
    # -------------------------------------------------------------------------

    title = await _ask_title()

    if title is None:
        Console.print(
            Console.Text("Announcement cancelled.").f_color_warning()
        )
        return

    # -------------------------------------------------------------------------
    # 5. Body
    # -------------------------------------------------------------------------

    body = await _ask_body()

    if body is None:
        Console.print(
            Console.Text("Announcement cancelled.").f_color_warning()
        )
        return

    # -------------------------------------------------------------------------
    # 6. Preview and confirmation
    # -------------------------------------------------------------------------

    _display_preview(
        title,
        body,
        len(recipients),
    )

    if not await _confirm_announcement():
        Console.print(
            Console.Text("Announcement cancelled.").f_color_warning()
        )
        return

    # -------------------------------------------------------------------------
    # 7. Send
    # -------------------------------------------------------------------------

    Console.print(
        Console.Text("\nSending announcement...\n").f_color_warning()
    )

    success, failed = await _send_announcement(
        recipients,
        title,
        body,
    )

    # -------------------------------------------------------------------------
    # 8. Summary
    # -------------------------------------------------------------------------

    Console.print(
        Console.Text("\nAnnouncement completed\n").f_style_bold()
        + Console.Text("  Successful: ").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
        + Console.Text(str(success)).f_style_bold().f_color_success()
        + "\n"
        + Console.Text("  Failed: ").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
        + Console.Text(str(failed)).f_style_bold().f_color_error()
        + "\n"
        + Console.Text("  Total: ").f_color_foreground(
            Console.ColorRGB(150, 150, 150)
        )
        + Console.Text(str(success + failed)).f_style_bold()
        + "\n"
    )
