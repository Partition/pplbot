import discord
from models.invite import Invite
from database import AsyncSessionLocal
from models.player import Player, PlayerAlreadyInTeam
from models.team import Team
import re

from utils.util_funcs import player_join_team

class ConfirmView(discord.ui.View):
    def __init__(self, timeout: float | None = None):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()


class InviteApprovalButton(discord.ui.DynamicItem[discord.ui.Button], template=r'invite_approval:(?P<action>approve|deny):(?P<id>[0-9]+)'):
    def __init__(self, invite_id: int, is_approve: bool):
        action = "approve" if is_approve else "deny"
        label = "Approve" if is_approve else "Deny"
        style = discord.ButtonStyle.green if is_approve else discord.ButtonStyle.red
        super().__init__(
            discord.ui.Button(
                label=label,
                style=style,
                custom_id=f'invite_approval:{action}:{invite_id}',
            )
        )
        self.invite_id: int = invite_id
        self.is_approve: bool = is_approve

    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        invite_id = int(match['id'])
        is_approve = match['action'] == 'approve'
        return cls(invite_id, is_approve)

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.handle_approval(interaction)

    async def handle_approval(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            invite = await Invite.fetch_from_id(session, self.invite_id)
            current_embed = interaction.message.embeds[0]

            if self.is_approve:
                current_embed.title = "Invite Approved"
                current_embed.color = discord.Color.green()
                current_embed.set_footer(text=f"Invite approved by {interaction.user.display_name}")
                    # TODO: Notify the inviter and invitee
            else:
                current_embed.title = "Invite Denied"
                current_embed.color = discord.Color.red()
                current_embed.set_footer(text=f"Invite denied by {interaction.user.display_name}")
                # TODO: Notify the inviter about the denial
                
            await Invite.approve_status(session, invite.id, self.is_approve)
            await session.commit()
            
            await interaction.message.edit(embed=current_embed, view=None)

class InviteApprovalView(discord.ui.View):
    def __init__(self, invite_id: int):
        super().__init__(timeout=None)
        self.add_item(InviteApprovalButton(invite_id, True))
        self.add_item(InviteApprovalButton(invite_id, False))