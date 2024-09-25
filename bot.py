from discord.ext import commands
import discord
from cogs.general import General
from cogs.admin import Admin
from cogs.team import TeamCog
from cogs.account import AccountCog
from cogs.error_handler import ErrorHandler
from database import init_db, get_db

import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.ERROR)

async def setup_bot():
    intents = discord.Intents.all()

    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        
        # Dynamically load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Loaded file: {filename[:-3]}')
                except Exception as e:
                    print(f'Failed to load file {filename[:-3]}: {e}')
        print("All files loaded")
        
        # Send a message to a specific channel
        channel_id = int(os.getenv('BOT_READY_CHANNEL_ID'))  # Get channel ID from .env file
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send("Bot is now online and ready!")
        else:
            print(f"Could not find channel with ID {channel_id}")

    return bot