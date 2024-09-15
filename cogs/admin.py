import discord
from discord.ext import commands

class Admin(commands.Cog):
    """
    Admin commands
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync", description="Sync the bot's commands")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        await self.bot.tree.sync()
        await ctx.send("Commands synced!")