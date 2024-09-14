from discord.ext import commands
from discord import app_commands
import discord

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! Latency: {latency}ms")
        
    @app_commands.command(name="sync", description="Sync the bot's commands")
    async def sync(self, interaction: discord.Interaction):
        await self.bot.tree.sync()
        await interaction.response.send_message("Commands synced!")
