import discord
from discord.ext import commands
from discord import app_commands
from models.team import Team
from models.player import Player, PlayerDoesNotExist
from models.invite import Invite
from models.transfer import Transfer
from database import AsyncSessionLocal
from utils.embed_gen import EmbedGenerator
from datetime import datetime, timedelta


@app_commands.guilds(911940380717617202)
class TeamCog(commands.GroupCog, group_name="team", description="Team management commands"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    # Interaction check to ensure user is registered
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        async with AsyncSessionLocal() as session:
            try: 
                player = await Player.fetch_from_discord_id(session, interaction.user.id)
            except PlayerDoesNotExist:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be registered to use this command."))
                return False
        return True

    @app_commands.command(name="invite", description="Invite a player to your team")
    async def invite(self, interaction: discord.Interaction, player: discord.Member):
        async with AsyncSessionLocal() as session:
            try:
                inviter = await Player.fetch_from_discord_id(session, interaction.user.id)
                invitee = await Player.fetch_from_discord_id(session, player.id)
            except PlayerDoesNotExist:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Player not found."))
                return
            
            if not inviter.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be in a team to invite players."))
                return
            
            if invitee.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="This player is already in a team."))
                return
            
            team = await Team.fetch_from_id(session, inviter.team_id)
            if team.captain_id != inviter.discord_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Only the team captain can invite players."))
                return
            
            expires_at = datetime.now() + timedelta(days=7)
            invite = await Invite.create(session, inviter.discord_id, invitee.discord_id, team.id, expires_at)
            # Invites will go through mod channel for approval (will be toggleable in config)
            
            
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Invite Sent", description=f"Invited {player.display_name} to your team."))

    @app_commands.command(name="invites", description="List all pending invites for your team")
    async def invites(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            
            if not player:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be registered to use this command."))
                return
            
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
            
            invite_list = "\n".join([f"<@{invite.invitee_id}> (Expires: {invite.expires_at.strftime('%Y-%m-%d %H:%M:%S')})" for invite in active_invites])
            await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Active Invites", description=invite_list))

    @app_commands.command(name="accept", description="Accept a team invitation")
    async def accept(self, interaction: discord.Interaction, team_name: str):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            
            if player.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You are already in a team."))
                return
            
            team = await Team.fetch_from_name(session, team_name)
            if not team:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Team not found."))
                return
            
            invite = await Invite.fetch_active_invites_by_invitee(session, player.discord_id)
            valid_invite = next((inv for inv in invite if inv.team_id == team.id), None)
            
            if not valid_invite:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="No valid invite found for this team."))
                return
            
            player.team_id = team.id
            await Invite.approve_status(session, valid_invite.id, True)
            await Transfer.create(session, player.discord_id, team.id, team.name, True)
            await session.commit()
            
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Invite Accepted", description=f"You have joined {team_name}."))

    @app_commands.command(name="decline", description="Decline a team invitation")
    async def decline(self, interaction: discord.Interaction, team_name: str):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            
            if not player:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be registered to use this command."))
                return
            
            team = await Team.fetch_from_name(session, team_name)
            if not team:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Team not found."))
                return
            
            invite = await Invite.fetch_active_invites_by_invitee(session, player.discord_id)
            valid_invite = next((inv for inv in invite if inv.team_id == team.id), None)
            
            if not valid_invite:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="No valid invite found for this team."))
                return
            
            await Invite.approve_status(session, valid_invite.id, False)
            
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Invite Declined", description=f"You have declined the invitation to join {team_name}."))

    @app_commands.command(name="leave", description="Leave your current team")
    async def leave(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            
            if not player:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be registered to use this command."))
                return
            
            if not player.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You are not in a team."))
                return
            
            team = await Team.fetch_from_id(session, player.team_id)
            if team.captain_id == player.discord_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Team captains cannot leave their team. Transfer ownership first."))
                return
            
            old_team_name = team.name
            await player.leave_team(session)
            await Transfer.create(session, player.discord_id, None, old_team_name, False)
            
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Team Left", description="You have left your team."))

    @app_commands.command(name="kick", description="Kick a player from your team")
    async def kick(self, interaction: discord.Interaction, player: discord.Member):
        async with AsyncSessionLocal() as session:
            kicker = await Player.fetch_from_discord_id(session, interaction.user.id)
            kicked = await Player.fetch_from_discord_id(session, player.id)
            
            if not kicker or not kicked:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Both players must be registered."))
                return
            
            if not kicker.team_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be in a team to kick players."))
                return
            
            team = await Team.fetch_from_id(session, kicker.team_id)
            if team.captain_id != kicker.discord_id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Only the team captain can kick players."))
                return
            
            if kicked.team_id != team.id:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="This player is not in your team."))
                return
            
            await kicked.leave_team(session)
            await Transfer.create(session, kicked.discord_id, None, team.name, False)
            
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Player Kicked", description=f"Kicked {player.display_name} from your team."))

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
            
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Ownership Transferred", description=f"Transferred team ownership to {new_owner.display_name}."))

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