import discord
from discord.ext import commands
from discord import app_commands
from database import AsyncSessionLocal
from models.team import Team
from models.player import Player, PlayerDoesNotExist
from models.transfer import Transfer
from models.team import TeamNameAlreadyExists, TeamTagAlreadyExists
from utils.embed_gen import EmbedGenerator


class Admin(commands.Cog):
    """
    Admin commands
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync", description="Sync the bot's commands")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        print("Sync command invoked")
        await self.bot.tree.sync()
        await ctx.send("Commands synced!")
        
    @commands.command(name="gsync", description="Sync the bot's commands to a specific guild")
    async def guildsync(self, ctx, guild_id: int):
        guild = discord.Object(id=guild_id)
        await self.bot.tree.sync(guild=guild)
        await ctx.send("Commands synced to guild!")
    
    @app_commands.command(name="team_create", description="Create a new team")
    @app_commands.describe(name="The name of the team", tag="The tag of the team", captain="The captain of the team")
    @app_commands.guilds(911940380717617202)
    async def create_team(self, interaction: discord.Interaction, name: str, tag: str, captain: discord.Member, league: str = None):
        async with AsyncSessionLocal() as session:
            try:
                player = await Player.fetch_from_discord_id(session, captain.id)
                if player.team_id:
                    await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Player is already in a team."))
                    return
                
                team = await Team.create(session, name, tag, player.discord_id, league)
                player.team_id = team.id
                await Transfer.create(session, player.discord_id, team.id, transfer_type=2)
                
                await session.commit()
                await interaction.response.send_message(embed=EmbedGenerator.success_embed(title="Team Created", description=f"Successfully created team {name} ({tag})."))
            
            except PlayerDoesNotExist:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be registered to use this command."))
            except TeamNameAlreadyExists:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"A team with the name '{name}' already exists."))
            except TeamTagAlreadyExists:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"A team with the tag '{tag}' already exists."))
            except Exception as e:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"An unexpected error occurred: {str(e)}"))

