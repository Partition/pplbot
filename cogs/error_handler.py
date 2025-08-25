from discord.ext import commands
import logging
from utils.embed_gen import EmbedGenerator
import discord
from config import BOT_CHANNEL

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            error_message = "Command not found."
        elif isinstance(error, commands.MissingPermissions):
            error_message = "You don't have the required permissions to use this command."
        elif isinstance(error, commands.MissingRequiredArgument):
            error_message = f"Missing required argument: `{error.param}`"
        else:
            error_message = f"An error occurred: `{str(error)}`"
            
        await ctx.send(embed=EmbedGenerator.error_embed(title="Error", description=error_message))
        logging.error(f"{error_message}")
        
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        error = args[0] if args else None
        # TODO: Send error to discord (config channel)
        channel = self.bot.get_channel(BOT_CHANNEL)
        await channel.send(embed=EmbedGenerator.error_embed(title="Error", description=f"An error occurred in {event}: {error}"))
        logging.error(f"An error occurred in {event}: {error}")
        
    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            error_message = f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds."
        elif isinstance(error, discord.app_commands.MissingPermissions):
            error_message = "You don't have the required permissions to use this command."
        else:
            error_message = f"An error occurred: {str(error)}"
        
        await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=error_message), ephemeral=True)
        logging.error(f"Slash command error: {error}")
        
async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))

