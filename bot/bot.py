from discord.ext import commands
import discord
from bot.commands.general import General
from bot.models import Player, Team, Account, Transfer, Invite, Strike
from bot.database import init_db, get_db
import os
from dotenv import load_dotenv

load_dotenv()

async def setup_bot():
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        await init_db()
        await bot.add_cog(General(bot))

        # Send a message to a specific channel
        channel_id = int(os.getenv('BOT_READY_CHANNEL_ID'))  # Get channel ID from .env file
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send("Bot is now online and ready!")
        else:
            print(f"Could not find channel with ID {channel_id}")

    return bot