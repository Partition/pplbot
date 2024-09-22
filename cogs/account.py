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
from datetime import datetime
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
            if not await Player.exists(session, interaction.user.id):
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="You are not registered, please use the /register command"), ephemeral=True)
        return True
    
    @app_commands.command(name="add", description="Add an account to the database")
    @app_commands.describe(username="The username of the account", tag="The tag of the account", server="The server of the account")
    async def add(self, interaction: discord.Interaction, username: str, tag: str, server: LeagueServer):
        
        # Check if the account already exists in database
        async with AsyncSessionLocal() as session:
            if await Account.check_if_username_and_tag_exists(session, username, tag, LeagueServer(server.value).name):
                print(await Account.check_if_username_and_tag_exists(session, username, tag, LeagueServer(server.value).name))
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Account already exists"), ephemeral=True)
        
        # Check if account is valid and fetch account info
        try:
            _, initial_summoner, _ = await get_account_info(username, tag, server.value)
            current_icon_id = initial_summoner["profileIconId"]
        except Exception as e:
            error_message = str(e)
            if "404" in error_message:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Account not found, please check the username and tag are correct"), ephemeral=True)
            else:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description=f"Error fetching account, share the error message with the developers: {error_message}"), ephemeral=True)
        
        # Get a random profile icon id that is not the current one
        random_id = choice([i for i in range(0, 20) if i != current_icon_id])
        url = f"https://ddragon.leagueoflegends.com/cdn/14.11.1/img/profileicon/{random_id}.png"
        
        # Send the confirmation message
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
            
            # Fetch the account info again to compare the profile icon with the random one
            updated_account, updated_summoner, updated_ranked = await get_account_info(username, tag, server.value)
            if updated_summoner["profileIconId"] != random_id:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Profile icon does not match"), ephemeral=True)
            
            # Create the account in the database with account data (+ solo queue ranked data IF available)
            async with AsyncSessionLocal() as session:
                account_data = {
                    "player_id": interaction.user.id,
                    "server": LeagueServer(server.value).name,  # Convert the enum to the server name, useful for op.gg links
                    "puuid": updated_account["puuid"],
                    "summoner_name": updated_account["gameName"],
                    "summoner_tag": updated_account["tagLine"],
                    "summoner_id": updated_summoner["id"],
                }

                if updated_ranked:
                    account_data.update({
                        "rank": updated_ranked["rank"],
                        "tier": updated_ranked["tier"],
                        "league_points": updated_ranked["leaguePoints"],
                        "wins": updated_ranked["wins"],
                        "losses": updated_ranked["losses"],
                        "peak_tier": updated_ranked["tier"],
                        "peak_league_points": updated_ranked["leaguePoints"],
                        "peak_occurence": datetime.now()
                    })

                account = await Account.create(session=session, **account_data)

                await session.commit()
            new_embed = EmbedGenerator.success_embed(title="Success", description="Account successfully added to the database")
        await interaction.edit_original_response(embed=new_embed, view=None)

