import discord
import jardiscordengine as JDE

from jarbot_modulable.constants import CONFIRMATION_TIMEOUT
from jarbot_modulable.services.generic import log_info


async def send_ephemeral(
        interaction: discord.Interaction,
        content: str,
        view: discord.ui.View | None = None,
    ) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(
            content,
            view=view,
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        content,
        view=view,
        ephemeral=True,
    )


async def change_student_role(
        ctx: JDE.Entities.JDEEntityApplicationContext,
        requested_role_id: int,
        opposite_role_id: int,
    ) -> None:
    interaction = ctx.interaction
    guild = interaction.guild

    if guild is None:
        await send_ephemeral(
            interaction,
            "This command can only be used in a server.",
        )
        return

    member = guild.get_member(interaction.user.id)

    if member is None:
        await send_ephemeral(
            interaction,
            "Unable to retrieve your server membership.",
        )
        return

    requested_role = guild.get_role(requested_role_id)
    opposite_role = guild.get_role(opposite_role_id)

    if requested_role is None or opposite_role is None:
        await send_ephemeral(
            interaction,
            "One or more configured roles could not be found.",
        )
        return

    if requested_role in member.roles:
        await send_ephemeral(
            interaction,
            "You already have this role.",
        )
        return

    view = RoleConfirmationView(
        member=member,
        requested_role=requested_role,
        opposite_role=opposite_role,
    )

    await send_ephemeral(
        interaction,
        (
            f"Are you sure you want to receive {requested_role.mention}?\n\n"
            "**Important:** Once confirmed, you cannot change your "
            "student role for 24 hours.\n\n"
            f"Your current {opposite_role.mention} role will be removed "
            "if you have it."
        ),
        view=view,
    )


class RoleConfirmationView(discord.ui.View):

    def __init__(
            self,
            member: discord.Member,
            requested_role: discord.Role,
            opposite_role: discord.Role,
        ) -> None:
        super().__init__(timeout=CONFIRMATION_TIMEOUT)

        self.member = member
        self.requested_role = requested_role
        self.opposite_role = opposite_role

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success,
    )
    async def confirm(
            self,
            button: discord.ui.Button,
            interaction: discord.Interaction,
        ) -> None:
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This confirmation does not belong to you.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild

        if guild is None:
            await interaction.edit_original_response(
                content="This command can only be used in a server.",
                view=None,
            )
            self.stop()
            return

        member = guild.get_member(self.member.id)

        if member is None:
            await interaction.edit_original_response(
                content="Unable to retrieve your server membership.",
                view=None,
            )
            self.stop()
            return

        if self.requested_role in member.roles:
            await interaction.edit_original_response(
                content="You already have this role.",
                view=None,
            )
            self.stop()
            return

        try:
            roles = [
                role
                for role in member.roles
                if role.id != self.opposite_role.id
            ]

            roles.append(self.requested_role)

            await member.edit(
                roles=roles,
                reason="Student role selection",
            )

        except discord.Forbidden:
            await interaction.edit_original_response(
                content="I don't have permission to manage these roles.",
                view=None,
            )
            self.stop()
            return

        except discord.HTTPException:
            await interaction.edit_original_response(
                content="An error occurred while updating your roles.",
                view=None,
            )
            self.stop()
            return

        log_info("Role given", f"{member.name} is now {self.requested_roles}")
        await interaction.edit_original_response(
            content=(
                f"You have successfully received "
                f"{self.requested_role.mention}!"
            ),
            view=None,
        )

        self.stop()

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger,
    )
    async def cancel(
            self,
            button: discord.ui.Button,
            interaction: discord.Interaction,
        ) -> None:
        if interaction.user.id != self.member.id:
            await interaction.response.send_message(
                "This confirmation does not belong to you.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        await interaction.edit_original_response(
            content="Role selection cancelled.",
            view=None,
        )

        self.stop()
