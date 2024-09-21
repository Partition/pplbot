import discord
from discord import app_commands
from discord.ext import commands
from models.player import Player, PlayerDoesNotExist
from utils.embed_gen import EmbedGenerator
from database import AsyncSessionLocal
from utils.views import ConfirmView
from utils.util_funcs import get_account_info
from models.account import Account
from random import choice
from enum import Enum

class LeagueServer(Enum):
    EUNE = "eun1"
    EUW = "euw1"

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
    @app_commands.describe(username="The username of the account", tag="The tag of the account", server="The server of the account")
    async def add(self, interaction: discord.Interaction, username: str, tag: str, server: LeagueServer):
        _, initial_summoner = await get_account_info(username, tag, server.value)
        current_icon_id = initial_summoner["profileIconId"]
        
        # Get a random profile icon id that is not the current one
        random_id = choice([i for i in range(0, 20) if i != current_icon_id])
        url = f"https://ddragon.leagueoflegends.com/cdn/14.11.1/img/profileicon/{random_id}.png"
        
        view = ConfirmView()
        await interaction.response.send_message(
            view=view,
            embed=EmbedGenerator.default_embed(title="Change account icon", description="Change the account's profile icon to the one shown to confirm ownership").set_thumbnail(url=url),
            ephemeral=True
        )
        await view.wait()

        if view.value is None or not view.value:
            new_embed = EmbedGenerator.error_embed(title="Error", description="You must confirm to change the account icon")
        else:
            updated_account, updated_summoner = await get_account_info(username, tag, server.value)
            if updated_summoner["profileIconId"] == random_id:
                async with AsyncSessionLocal() as session:
                    account = await Account.create(
                        session = session,
                        player_id = interaction.user.id,
                        server = LeagueServer(server.value).name, # Convert the enum to the server name, useful for op.gg links
                        puuid = updated_account["puuid"],
                        summoner_name = updated_account["gameName"],
                        summoner_tag = updated_account["tagLine"],
                    )
                    await session.commit()
                new_embed = EmbedGenerator.success_embed(title="Success", description="Account successfully confirmed")
            else:
                new_embed = EmbedGenerator.error_embed(title="Error", description="Profile icon does not match")
        
        await interaction.edit_original_response(embed=new_embed, view=None)

