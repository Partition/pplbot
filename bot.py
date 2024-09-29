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

from utils.views import InviteApprovalView

load_dotenv()
logging.basicConfig(level=logging.ERROR)

class PPLBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        self.add_view(InviteApprovalView(0))
        await self.load_cogs()

    async def load_cogs(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Loaded file: {filename[:-3]}')
                except Exception as e:
                    print(f'Failed to load file {filename[:-3]}: {e}')
        print("All files loaded")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        
        channel_id = int(os.getenv('BOT_READY_CHANNEL_ID'))
        channel = self.get_channel(channel_id)
        if channel:
            await channel.send("Bot is now online and ready!")
        else:
            print(f"Could not find channel with ID {channel_id}")

async def setup_bot():
    return PPLBot()
