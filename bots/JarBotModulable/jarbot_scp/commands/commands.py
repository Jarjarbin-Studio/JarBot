import jardiscordengine as JDE

from jarbot_scp.constants import PGE_ROLE, BACH_ROLE
from jarbot_scp.services.funny_helpers import get_funny
from jarbot_scp.services.role_helpers import change_student_role


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


def register_commands(
        bot: JDE.Bots.JDEBot
    ) -> None:
    bot.command_manager.register_commands(
        funny,
        pge,
        bach,
    )
