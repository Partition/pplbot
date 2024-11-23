import discord
from discord.ext import commands
from discord import app_commands
from database import AsyncSessionLocal
from models.team import Team
from models.player import Player
from models.transfer import Transfer
from models.team import TeamNameAlreadyExists, TeamTagAlreadyExists
from utils.embed_gen import EmbedGenerator
from utils.enums import TeamLeague, TransferType
from utils.util_funcs import player_join_team, player_leave_team
from utils.views import ConfirmView
from config import GUILD_ID, TAG_CHARACTER_LIMIT

class Admin(commands.Cog):
    """
    Admin commands
    """
    def __init__(self, bot):
        self.bot = bot

    # Interaction check to ensure user is registered
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        async with AsyncSessionLocal() as session:
            if not await Player.exists(session, interaction.user.id):
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You are not registered, please use the /register command"), ephemeral=True)
        return True
    
    @commands.command(name="sync", description="Sync the bot's commands")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        print("Sync command invoked")
        cmds = await self.bot.tree.sync()
        await ctx.send(f"Commands synced! {len(cmds)} commands synced.")
        
    @commands.command(name="gsync", description="Sync the bot's commands to a specific guild")
    async def guildsync(self, ctx, guild_id: int):
        guild = discord.Object(id=guild_id)
        cmds = await self.bot.tree.sync(guild=guild)
        await ctx.send(f"Commands synced! {len(cmds)} commands synced.")
    
    @app_commands.command(name="create_team", description="Create a new team")
    @app_commands.describe(name="The name of the team", tag="The tag of the team", captain="The captain of the team", league="The league of the team")
    @app_commands.guilds(911940380717617202)
    async def create_team(self, interaction: discord.Interaction, name: str, tag: str, captain: discord.Member, league: TeamLeague = None):
        try:
            async with AsyncSessionLocal() as session:
                player = await Player.fetch_from_discord_id(session, captain.id)
                if not player:
                    return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Player does not exist."))
                
                if player.team_id:
                    return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Player is already in a team."))
                
                if len(tag) > TAG_CHARACTER_LIMIT:
                    return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"Tag must be less than {TAG_CHARACTER_LIMIT} characters."))
                
                league = league.value if league else None
                team = await Team.create(session, name, tag, player.discord_id, league)
                await interaction.guild.create_role(name=name, hoist=True, mentionable=True, reason="Team created by " + interaction.user.name)
                
                success, message = await player_join_team(session, interaction, player, team, TransferType.TEAM_CREATE)
                if not success:
                    return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=message))
                await session.commit()
            
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Team Created", description=f"Successfully created **{name} ({tag})** [{league}]"))
        except TeamNameAlreadyExists:
            await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"A team with the name '{name}' already exists."))
        except TeamTagAlreadyExists:
            await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"A team with the tag '{tag}' already exists."))
        except Exception as e:
            await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"An unexpected error occurred: {str(e)}"))

    @app_commands.command(name="create_channels", description="Create all team channels and category")
    @app_commands.describe(team_tag="The tag of the team")
    @app_commands.guilds(911940380717617202)
    async def create_channels(self, interaction: discord.Interaction, team_tag: str):
        async with AsyncSessionLocal() as session:
            team = await Team.fetch_from_tag(session, team_tag)
            if not team:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"Team with tag '{team_tag}' does not exist."))
        
        role = discord.utils.get(interaction.guild.roles, name=team.name)
        if not role:
            return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"Role '{team.name}' does not exist."))
        
        category_channel = discord.utils.get(interaction.guild.categories, name=team.name)
        if category_channel:
            return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"Category channel '{team.name}' already exists."))
        
        text_overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role: discord.PermissionOverwrite(read_messages=True),
        }
        voice_overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
            role: discord.PermissionOverwrite(connect=True),
        }
        
        category_channel = await interaction.guild.create_category(name=team.name, reason="Team category created by " + interaction.user.name)
        team_text_channel = await interaction.guild.create_text_channel(name=team.name, category=category_channel, overwrites=text_overwrites, reason="Team chat created by " + interaction.user.name)
        team_voice_channel = await interaction.guild.create_voice_channel(name=team.name, category=category_channel, overwrites=voice_overwrites, reason="Team voice channel created by " + interaction.user.name)
        await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Team Channels Created", description=f"Successfully created channels for team {team.name}."))
    
    @app_commands.command(name="editleague", description="Edit the league of a team")
    @app_commands.describe(search_term="The tag or name of the team", league="The league of the team to edit to")
    @app_commands.guilds(911940380717617202)
    async def edit_league(self, interaction: discord.Interaction, search_term: str, league: TeamLeague):
        async with AsyncSessionLocal() as session:
            teams = await Team.search_by_name_or_tag_in_league(session, search_term)
            if not teams:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"No teams found with tag or name '{search_term}'."))
            team = teams[0]
            team.league = league.value
            await session.commit()
            await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Team League Edited", description=f"Successfully edited the league of team **{team.name} ({team.tag})** to **{league.value}**."))
    
    @app_commands.command(name="archive", description="Archive a team")
    @app_commands.describe(search_term="The tag or name of the team")
    @app_commands.guilds(911940380717617202)
    async def archive(self, interaction: discord.Interaction, search_term: str):
        await interaction.response.defer()
        async with AsyncSessionLocal() as session:
            teams = await Team.search_by_name_or_tag_in_league(session, search_term)
            if not teams:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"Team with tag or name '{search_term}' does not exist."))
            team = teams[0]
            
            # Confirm with the user
            confirm_view = ConfirmView()
            view_msg = await interaction.followup.send(
                view=confirm_view,
                embed=EmbedGenerator.default_embed(title="Archive Team", description=f"Are you sure you want to archive team **{team.name} ({team.tag})**? This action cannot be undone."),
            )
            
            # Wait for user confirmation
            await confirm_view.wait()
            if confirm_view.value is None or not confirm_view.value:
                return await interaction.followup.edit_message(view_msg.id, embed=EmbedGenerator.error_embed(title="Archive Team", description="Action cancelled by user."), view=None)
            
            category_channel = discord.utils.get(interaction.guild.categories, name=team.name)
            if category_channel:
                await category_channel.delete()
                
            text_channel = discord.utils.get(interaction.guild.text_channels, name=team.name)
            if text_channel:
                await text_channel.delete()
            
            voice_channel = discord.utils.get(interaction.guild.voice_channels, name=team.name)
            if voice_channel:
                await voice_channel.delete()
            
            players = await Player.fetch_all_from_team_id(session, team.id)
            for player in players:
                await player_leave_team(session, interaction, player, team, TransferType.TEAM_DISBAND)
            
            role = discord.utils.get(interaction.guild.roles, name=team.name)
            if role:
                await role.delete()
                
            await Team.archive(session, team.id)
            await session.commit()
            await interaction.followup.edit_message(view_msg.id, embed=EmbedGenerator.success_embed(title="Team Archived", description=f"Successfully archived team **{team.name} ({team.tag})**. All related channels have been deleted."),
                                                     view=None)
    @app_commands.command()
    @commands.has_permissions(administrator=True)
    async def stop(self, interaction: discord.Interaction):
        """Stop the bot and unloads all cogs.
        """

        await interaction.response.send_message("Stopping the bot...")
        await self.bot.close()
        
async def setup(bot):
    await bot.add_cog(Admin(bot), guilds=[discord.Object(id=GUILD_ID)])
