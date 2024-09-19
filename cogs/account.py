import discord
from discord import app_commands
from discord.ext import commands
from models.player import Player, PlayerDoesNotExist
from models.team import Team
from models.invite import Invite
from utils.embed_gen import EmbedGenerator
from database import AsyncSessionLocal
from datetime import datetime, timedelta
from pulsefire.clients import RiotAPIClient
from dotenv import load_dotenv

import os

load_dotenv()

@app_commands.guilds(911940380717617202)


class AccountCog(commands.GroupCog, group_name="account", description="Account management commands"):
    def __init__(self, bot):
        self.bot = bot
        super().__init__()
    
    # Interaction check to ensure user is registered
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        async with AsyncSessionLocal() as session:
            try: 
                player = await Player.fetch_from_discord_id(session, interaction.user.id)
            except PlayerDoesNotExist:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You must be registered to use this command."))
                return False
        return True
    
    
    @app_commands.command(name="add", description="Add an account to the database")
    async def add(self, interaction: discord.Interaction, username: str, tag: str, server: str):
        async with RiotAPIClient(default_headers={"X-Riot-Token": os.getenv("RIOT_API_KEY")}) as client: 
            account = await client.get_account_v1_by_riot_id(region="europe", game_name=username, tag_line=tag)
            puuid, game_name, tag_line = account["puuid"], account["gameName"], account["tagLine"]
            summoner = await client.get_lol_summoner_v4_by_puuid(region="euw1", puuid=account["puuid"])
            puuid, name, profile_icon_id = summoner["id"], summoner["name"], summoner["profileIconId"]
            await interaction.response.send_message(f"Account added: \n{puuid}\n{name}\n{profile_icon_id}\n{game_name}\n{tag_line}")
            
            # Verifiy account ownership with profile icon id
