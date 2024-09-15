import discord
from discord.ext import commands

class Admin(commands.Cog):
    """
    Admin commands
    """
    def __init__(self, bot):
        self.bot = bot
        print("Admin cog loaded")  # Debug print

    @commands.command(name="sync", description="Sync the bot's commands")
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx):
        print("Sync command invoked")  # Debug print
        await self.bot.tree.sync()
        await ctx.send("Commands synced!")
        
    @commands.command(name="gsync", description="Sync the bot's commands to a specific guild")
    async def guildsync(self, ctx, guild_id: int):
        guild = discord.Object(id=guild_id)
        await self.bot.tree.sync(guild=guild)
        await ctx.send("Commands synced to guild!")
