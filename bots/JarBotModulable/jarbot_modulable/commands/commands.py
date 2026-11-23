import discord
import jardiscordengine as JDE

from jarbot_modulable.constants import PGE_ROLE, BACH_ROLE, MAN_CHANNEL
from jarbot_modulable.services import mankier
from jarbot_modulable.services.funny import get_funny
from jarbot_modulable.services.generic import log_info
from jarbot_modulable.services.role import change_student_role


@JDE.Commands.command(
    name="funny",
    description="Get a random funny quote and joke",
)
@JDE.Commands.cooldown(
    rate=1,
    per=5,
    scope="guild",
)
@JDE.Commands.guild_only()
async def funny(
        bot: JDE.Bots.JDEBot,
        ctx: JDE.Entities.JDEEntityApplicationContext
    ) -> None:
    await ctx.defer()
    await ctx.interaction.followup.send(get_funny())


@JDE.Commands.command(
    name="pge",
    description="Get PGE role (remove Bachelor role if owned)",
)
@JDE.Commands.cooldown(
    rate=1,
    per=86400,
    scope="user",
)
@JDE.Commands.bot_has_permissions(
    manage_roles=True
)
@JDE.Commands.guild_only()
async def pge(
        bot: JDE.Bots.JDEBot,
        ctx: JDE.Entities.JDEEntityApplicationContext
    ) -> None:
    await ctx.defer(ephemeral=True)
    await change_student_role(
        ctx,
        requested_role_id=PGE_ROLE.id,
        opposite_role_id=BACH_ROLE.id,
    )


@JDE.Commands.command(
    name="bach",
    description="Get Bachelor role (remove PGE role if owned)",
)
@JDE.Commands.cooldown(
    rate=1,
    per=86400,
    scope="user",
)
@JDE.Commands.bot_has_permissions(
    manage_roles=True
)
@JDE.Commands.guild_only()
async def bach(
        bot: JDE.Bots.JDEBot,
        ctx: JDE.Entities.JDEEntityApplicationContext
    ) -> None:
    await change_student_role(
        ctx,
        requested_role_id=BACH_ROLE.id,
        opposite_role_id=PGE_ROLE.id,
    )


@JDE.Commands.command(
    name="man",
    description="Search and retrieve Linux manual pages",
)
@JDE.Commands.option(
    name="query",
    description="Manual name",
    option_type=str,
    required=True,
    max_length=100,
)
@JDE.Commands.option(
    name="section",
    description="Manual section",
    option_type=int,
    required=False,
    min_value=1,
    max_value=9,
)
@JDE.Commands.option(
    name="posix",
    description="Search in POSIX manual pages",
    option_type=bool,
    required=False,
)
@JDE.Commands.option(
    name="hidden",
    description="Only show the response to yourself",
    option_type=bool,
    required=False,
)
@JDE.Commands.cooldown(
    rate=1,
    per=5,
    scope="user",
)
@JDE.Commands.guild_only()
async def man(
        bot: JDE.Bots.JDEBot,
        ctx: JDE.Entities.JDEEntityApplicationContext,
        query: str,
        section: int = 0,
        posix: bool = False,
        hidden: bool = False,
    ) -> None:
    if ctx.channel.id != MAN_CHANNEL.id:
        await ctx.interaction.response.send_message(
            f"This command can only be used in {MAN_CHANNEL.name} ({MAN_CHANNEL.id}).",
            ephemeral=True,
        )
        return

    await ctx.defer(ephemeral=hidden)

    section = f".{section}" if section else ""
    posix = "p" if posix else ""
    query = f"{query}{section}{posix}"

    try:
        pages = await mankier.get_man_response(query)

        await mankier.send_man_response(
            ctx.interaction,
            pages,
            ephemeral=hidden,
        )

    except mankier.ManKierError as error:
        await ctx.interaction.followup.send(
            f"**ManKier API error**\n```{error}```",
            ephemeral=hidden,
        )

    except discord.HTTPException as error:
        log_info(
            "ManKier",
            f"Unable to send response through Discord: {error}",
        )

    else:
        log_info("ManKier", f"Manual page retrieved: {query!r}")


def register_commands(
        bot: JDE.Bots.JDEBot
    ) -> None:
    bot.command_manager.register_commands(
        funny,
        pge,
        bach,
        man,
    )
