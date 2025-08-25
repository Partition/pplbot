import discord
from models.invite import Invite
from database import AsyncSessionLocal
import re
from typing import Dict, List
from discord import app_commands
from discord.ext import commands

from utils.embed_gen import EmbedGenerator
from utils.util_funcs import send_dm

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
                # Notify the inviter that the invite has been approved
                inviter_embed = EmbedGenerator.success_embed(title="Invite Approved", description=f"Your invitation of **{invite.invitee.nickname}** to **{invite.team.name}** has been approved by {interaction.user.mention}.")
                await send_dm(interaction, interaction.guild.get_member(invite.inviter.discord_id), inviter_embed)
                # Notify the invitee that they have been invited
                team_invitation_embed = EmbedGenerator.default_embed(title="Team Invitation", description=f"You have been invited to join **{invite.team.name}** by {interaction.user.mention}.")  
                await send_dm(interaction, interaction.guild.get_member(invite.invitee.discord_id), team_invitation_embed)
            else:
                current_embed.title = "Invite Denied"
                current_embed.color = discord.Color.red()
                current_embed.set_footer(text=f"Invite denied by {interaction.user.display_name}")
                # Notify the inviter about the denial
                denial_embed = EmbedGenerator.error_embed(title="Invite Denial", description=f"Your invitation of **{invite.invitee.nickname}** to **{invite.team.name}** has been denied by {interaction.user.mention}.")
                await send_dm(interaction, interaction.guild.get_member(invite.inviter.discord_id), denial_embed)
                
            await Invite.approve_status(session, invite.id, self.is_approve)
            await session.commit()
            await interaction.message.edit(embed=current_embed, view=None)

class InviteApprovalView(discord.ui.View):
    def __init__(self, invite_id: int):
        super().__init__(timeout=None)
        self.add_item(InviteApprovalButton(invite_id, True))
        self.add_item(InviteApprovalButton(invite_id, False))
        
class CategorySelect(discord.ui.Select):
    def __init__(self, cogs: Dict[str, commands.Cog]):
        self.cogs = cogs
        self.selected_cog = None
        options = [
            discord.SelectOption(
                label="General Category",
                description="Contains general commands",
                emoji="⚙️",
                value="General"
            ),
            discord.SelectOption(
                label="Account Category",
                description="Contains account management commands",
                emoji="👥",
                value="AccountCog"
            ),
            discord.SelectOption(
                label="Team Category",
                description="Contains team management commands",
                emoji="🏆",
                value="TeamCog"
            ),

        ]
        super().__init__(
            placeholder="Select a category...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.selected_cog = self.values[0]
        commands = [c for c in self.cogs[self.selected_cog].walk_app_commands()]
        
        if not commands:
            embed = discord.Embed(
                title=f"{self.selected_cog} Commands",
                description="No commands found in this category.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title=f"{self.selected_cog} Commands",
                color=discord.Color.blue()
            )
            
            for cmd in commands:
                embed.add_field(
                    name=f"/{cmd.name} {' '.join([f'`{p.name}`' for p in cmd.parameters]) if cmd.parameters else ''}",
                    value=cmd.description or "No description available",
                    inline=False
                )

        await interaction.response.edit_message(embed=embed)

class HelpView(discord.ui.View):
    def __init__(self, cogs: Dict[str, commands.Cog]):
        super().__init__()
        self.add_item(CategorySelect(cogs))