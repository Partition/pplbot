import math
import discord
from discord.ext import commands
from discord import app_commands
from models.team import Team
from models.player import Player
from models.invite import Invite
from database import AsyncSessionLocal
from utils.embed_gen import EmbedGenerator
from datetime import datetime, timedelta
from config import APPROVAL_REQUIRED, INVITE_CHANNEL
from utils.paginator import ButtonPaginator
from utils.util_funcs import get_discord_unix_timestamp_long, player_join_team, player_leave_team, send_dm
from utils.views import InviteApprovalView

@app_commands.guilds(911940380717617202)
class TeamCog(commands.GroupCog, group_name="team", description="Team management commands"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    # Interaction check to ensure user is registered
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        async with AsyncSessionLocal() as session:
            if not await Player.exists(session, interaction.user.id):
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be registered to use this command."))
                return False
        return True

    @app_commands.command(name="invite", description="Invite a player to your team")
    async def invite(self, interaction: discord.Interaction, member: discord.Member):
        async with AsyncSessionLocal() as session:
            inviter = await Player.fetch_from_discord_id(session, interaction.user.id)
            invitee = await Player.fetch_from_discord_id(session, member.id)
            team = await Team.fetch_from_id(session, inviter.team_id)
            if not invitee:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Player is not registered."))
                return
            
            if not inviter.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be in a team to invite players."))
                return
            
            if invitee.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="This player is already in a team."))
                return
            
            if not inviter.is_captain:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Only the team captain can invite players."))
                return
            
            if await Invite.fetch_active_invite_by_team_id_and_invitee(session, inviter.team_id, invitee.discord_id):
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="This player has already been invited to this team."))
                return
            
            expires_at = datetime.now() + timedelta(days=7)
            invite = await Invite.create(session, inviter.discord_id, invitee.discord_id, inviter.team_id, expires_at)
            await session.commit()
            
        # Invites will go through mod channel for approval (will be toggleable in config)
        mod_invite_channel = self.bot.get_channel(INVITE_CHANNEL)
        if APPROVAL_REQUIRED:
            # Notify interaction user that invite has been sent and is awaiting approval
            response_message = EmbedGenerator.default_embed(title="Invite Needs Approval", description=f"Your invitation of {member.display_name} to {team.name} needs approval. Please wait for approval.")
            await interaction.response.send_message(embed=response_message)

            approval_embed = EmbedGenerator.default_embed(title="Invite Approval", description=f"Team: {team.name}\nInviter: {interaction.user.mention}\nInvitee: {member.mention}\nExpires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            view = InviteApprovalView(invite.id)
            await mod_invite_channel.send(embed=approval_embed, view=view)
        else:
            await Invite.approve_status(session, invite.id, True)
            await session.commit()
            
            # Notify interaction user that invite was sent
            response_message = EmbedGenerator.default_embed(title="Invite Sent", description=f"Invited {member.display_name} to your team.")
            await interaction.response.send_message(embed=response_message)
            
            # Notify invitee that they have been invited
            team_invitation_embed = EmbedGenerator.default_embed(title="Team Invitation", description=f"You have been invited to join **{team.name}** by {interaction.user.nick}.")  
            await send_dm(interaction, member, team_invitation_embed)
            
    @app_commands.command(name="invites", description="List all pending invites for your team")
    async def invites(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            
            if not player.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be in a team to view invites."))
                return
            
            team = await Team.fetch_from_id(session, player.team_id)
            if team.captain_id != player.discord_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Only the team captain can view invites."))
                return
            
            active_invites = await Invite.fetch_active_invites_by_inviter(session, player.discord_id)
            
            if not active_invites:
                await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Invites", description="No active invites found."))
                return
            
            per_page = 5
            amount_of_pages = math.ceil(len(active_invites) / per_page)
            pages = [EmbedGenerator.default_embed(
                title=f"Invite list - {team.name}", 
                description="\n".join([f"- <@{invite.invitee_id}> (Expires: {get_discord_unix_timestamp_long(invite.expires_at)})" for invite in active_invites[i*per_page:(i+1)*per_page]])) for i in range(amount_of_pages)]
            if amount_of_pages > 1:
                paginator = ButtonPaginator(pages)
                await paginator.start(interaction)
                return
            await interaction.response.send_message(embed=pages[0])

    @app_commands.command(name="accept", description="Accept a team invitation")
    async def accept(self, interaction: discord.Interaction, team_tag: str):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            
            if player.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You are already in a team."))
                return
            
            team = await Team.fetch_from_tag(session, team_tag)
            if not team:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Team not found."))
                return
            
            invite = await Invite.fetch_active_invite_by_team_tag_and_invitee(session, team.tag, player.discord_id)
            if not invite:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="No valid invite found for this team."))
                return
                    
            success, message = await player_join_team(session, interaction, player, team)
        
            if not success:
                embed = EmbedGenerator.error_embed(title="Invite Acceptance Failed", description=f"Could not add player to team: {message}")
                await interaction.response.send_message(embed=embed)
                return
            
            await Invite.accept_invite(session, invite.id)
            await session.commit()
            
            if "Database updated" in message:
                embed = EmbedGenerator.warning_embed(title="Invite Partially Accepted", description=f"You have joined **{team.name}** in the database, but: {message}")
            else:
                embed = EmbedGenerator.success_embed(title="Invite Accepted", description=f"You have joined **{team.name}**.")
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="kick", description="Kick a player from your team")
    async def kick(self, interaction: discord.Interaction, member: discord.Member):
        async with AsyncSessionLocal() as session:
            kicker = await Player.fetch_from_discord_id(session, interaction.user.id)
            kicked = await Player.fetch_from_discord_id(session, member.id)
            
            if not kicked:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Player is not registered."))
                return
            
            if not kicker.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be in a team to kick players."))
                return
            
            if kicked.discord_id == kicker.discord_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You cannot kick yourself."))
                return
            
            team = await Team.fetch_from_id(session, kicker.team_id)
            if team.captain_id != kicker.discord_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Only the team captain can kick players."))
                return
            
            if kicked.team_id != team.id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="This player is not in your team."))
                return
            
            success, message = await player_leave_team(session, interaction, kicked, team)
            
            if not success:
                embed = EmbedGenerator.error_embed(title="Kick Failed", description=f"Could not kick player from team: {message}")
                await interaction.response.send_message(embed=embed)
                return
            
            if "Database updated" in message:
                embed = EmbedGenerator.warning_embed(title="Kick Partially Successful", description=f"Player removed from team in database, but: {message}")
            else:
                embed = EmbedGenerator.success_embed(title="Player Kicked", description=f"Kicked {member.display_name} from your team. {message}")
            
            await interaction.response.send_message(embed=embed)
            
    @app_commands.command(name="decline", description="Decline a team invitation")
    async def decline(self, interaction: discord.Interaction, team_tag: str):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            
            team = await Team.fetch_from_tag(session, team_tag)
            if not team:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Team not found."))
                return
            
            invite = await Invite.fetch_active_invite_by_team_tag_and_invitee(session, team.tag, player.discord_id)
            if not invite:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="No valid invite found for this team."))
                return
            
            # Notify inviter that invite has been declined
            denial_embed = EmbedGenerator.default_embed(title="Invite Declined", description=f"Your invitation of **{player.nickname}** to **{team.name}** has been declined by {player.nickname}.")
            await send_dm(interaction, invite.inviter, denial_embed)
            
            await Invite.decline_invite(session, invite.id)
            await session.commit()
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Invite Declined", description=f"You have declined the invitation to join **{team.name}**."))

    @app_commands.command(name="leave", description="Leave your current team")
    async def leave(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            
            if not player.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You are not in a team."))
                return
            
            if await Player.is_captain(session, player.discord_id):
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Team captains cannot leave their team. Transfer ownership first."))
                return
            
            team = await Team.fetch_from_id(session, player.team_id)
            
            success, message = await player_leave_team(session, interaction, player, team)
            
            if not success:
                embed = EmbedGenerator.error_embed(title="Leave Failed", description=f"Could not leave team: {message}")
                await interaction.response.send_message(embed=embed)
                return
            
            if "Database updated" in message:
                embed = EmbedGenerator.warning_embed(title="Leave Partially Successful", description=f"You have left the team in the database, but: {message}")
            else:
                embed = EmbedGenerator.success_embed(title="Team Left", description=f"You have left **{team.name}**.")
            
            await interaction.response.send_message(embed=embed)
            
    @app_commands.command(name="transfer", description="Transfer team ownership to another player")
    async def transferownership(self, interaction: discord.Interaction, new_owner: discord.Member):
        async with AsyncSessionLocal() as session:
            current_captain = await Player.fetch_from_discord_id(session, interaction.user.id)
            new_captain = await Player.fetch_from_discord_id(session, new_owner.id)
            
            if not current_captain or not new_captain:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Both players must be registered."))
                return
            
            if not current_captain.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be in a team to transfer ownership."))
                return
            
            team = await Team.fetch_from_id(session, current_captain.team_id)
            if team.captain_id != current_captain.discord_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Only the team captain can transfer ownership."))
                return
            
            if new_captain.team_id != team.id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="The new owner must be in your team."))
                return
            
            team.captain_id = new_captain.discord_id
            await session.flush()
            
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Ownership Transferred", description=f"Transferred team ownership to {new_owner.mention}."))

    @app_commands.command(name="announce", description="Make an announcement to your team")
    async def announce(self, interaction: discord.Interaction, message: str):
        # Implementation for announce command
        await interaction.response.send_message(f"Announcement sent to your team: {message}")

    @app_commands.command(name="list", description="List all teams or members of a specific team")
    async def list(self, interaction: discord.Interaction, team_name: str = None):
        async with AsyncSessionLocal() as session:
            if team_name:
                team = await Team.fetch_from_name(session, team_name)
                if not team:
                    await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Team not found."))
                    return
                
                members = await Player.fetch_all_from_team_id(session, team.id)
                member_list = "\n".join([f"<@{member.discord_id}> ({member.role})" for member in members])
                await interaction.response.send_message(embed=EmbedGenerator.default_embed(title=f"Members of {team_name}", description=member_list))
            else:
                teams = await Team.fetch_all(session)
                team_list = "\n".join([f"{team.name} ({team.tag})" for team in teams])
                await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="All Teams", description=team_list))
                
async def setup(bot):
    await bot.add_cog(TeamCog(bot))