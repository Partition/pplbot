from discord.ext import commands
from discord import app_commands
import discord
from utils.embed_gen import EmbedGenerator
from models.player import Player
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from config import LANE_ROLES

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency")
    @app_commands.guilds(911940380717617202)
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Pong!", description=f"Latency: {latency}ms"))
        
    @app_commands.command(name="register", description="Register to the database")
    @app_commands.guilds(911940380717617202)
    async def register(self, interaction: discord.Interaction):
        member_roles = [role.name for role in interaction.user.roles]
        lane_role = list(filter(lambda x: x in LANE_ROLES, member_roles))
        
        if not lane_role:
            await interaction.response.send_message(
                embed=EmbedGenerator.error_embed(
                    title="Registration Failed",
                    description="You must have a lane role to register."
                )
            )
            return
        
        async with AsyncSessionLocal() as session:
            # Create a new player
            new_player = await Player.create(
                session,
                discord_id=interaction.user.id,
                role=lane_role[0]
            )

            await interaction.response.send_message(
                embed=EmbedGenerator.success_embed(
                    title="Registration Successful",
                    description=f"Welcome, {interaction.user.name}! You have been registered."
                )
            )

