import discord
from discord import app_commands
from discord.ext import commands
from models.player import Player, PlayerDoesNotExist
from utils.embed_gen import EmbedGenerator
from database import AsyncSessionLocal
from utils.views import ConfirmView
from utils.util_funcs import get_account_info, get_account_info_from_puuid
from models.account import Account
from random import choice
from enum import Enum
from datetime import datetime

class LeagueTier(Enum):
    IRON = 0
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    EMERALD = 5
    DIAMOND = 6
    MASTER = 7
    GRANDMASTER = 8
    CHALLENGER = 9

class LeagueRank(Enum):
    I = 4
    II = 3
    III = 2
    IV = 1

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

        # if/else creates the embed based on the view value
        if view.value is None or not view.value:
            new_embed = EmbedGenerator.error_embed(title="Error", description="You must confirm to change the account icon")
        else:
            # Fetch the account info again to compare the profile icon with the random one
            updated_account, updated_summoner, updated_ranked = await get_account_info(username, tag, server.value)
            if updated_summoner["profileIconId"] != random_id:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(title="Error", description="Profile icon does not match"), ephemeral=True)
            
            # Create dict with data to create the account in the database
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
                    "peak_rank": updated_ranked["rank"],
                    "peak_league_points": updated_ranked["leaguePoints"],
                    "peak_occurence": datetime.now()
                })
            
            # Create the account in the database
            async with AsyncSessionLocal() as session:
                account = await Account.create(session=session, **account_data)
                await session.commit()

            new_embed = EmbedGenerator.success_embed(title="Success", description="Account successfully added to the database")
            
        await interaction.edit_original_response(embed=new_embed, view=None)

    @app_commands.command(name="update", description="Update all your registered accounts")
    async def update(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        async with AsyncSessionLocal() as session:
            accounts = await Account.fetch_all_from_player_id(session, interaction.user.id)
            
            if not accounts:
                return await interaction.followup.send(embed=EmbedGenerator.error_embed(title="Error", description="You don't have any registered accounts to update."))
            
            updated_count = 0
            for account in accounts:
                
                # Only keeping try/except for the riot api call, in case a player transfers accounts between servers (will likely raise error)
                try:
                    updated_account, updated_summoner, updated_ranked = await get_account_info_from_puuid(account.puuid, LeagueServer[account.server].value)
                    account.summoner_name = updated_account["gameName"]
                    account.summoner_tag = updated_account["tagLine"]
                    account.summoner_id = updated_summoner["id"]
                    account.last_updated = datetime.now()
                    
                    if updated_ranked:
                        account.tier = updated_ranked["tier"]
                        account.rank = updated_ranked["rank"]
                        account.league_points = updated_ranked["leaguePoints"]
                        account.wins = updated_ranked["wins"]
                        account.losses = updated_ranked["losses"]
                        
                        # Update peak if current rank is higher
                        # If current tier is higher, update peak
                        # If current tier is same but current rank is higher, update peak
                        # If current tier is same, current rank is same but current lp is higher, update peak
                        if (LeagueTier[updated_ranked["tier"]].value > LeagueTier[account.peak_tier].value) or \
                           (LeagueTier[updated_ranked["tier"]].value == LeagueTier[account.peak_tier].value and \
                            LeagueRank[updated_ranked["rank"]].value > LeagueRank[account.peak_rank].value) or \
                            (LeagueTier[updated_ranked["tier"]].value == LeagueTier[account.peak_tier].value and \
                            LeagueRank[updated_ranked["rank"]].value == LeagueRank[account.peak_rank].value and \
                            updated_ranked["leaguePoints"] > account.peak_league_points):
                            account.peak_tier = updated_ranked["tier"]
                            account.peak_rank = updated_ranked["rank"]
                            account.peak_league_points = updated_ranked["leaguePoints"]
                            account.peak_occurence = datetime.now()
                    
                    updated_count += 1
                except Exception as e:
                    print(f"Error updating account {account.summoner_name}#{account.summoner_tag}: {str(e)}")
            
            await session.commit()
        
        if updated_count == 0:
            embed = EmbedGenerator.error_embed(title="Update Failed", description="Failed to update any accounts. Please try again later.")
        else:
            embed = EmbedGenerator.success_embed(title="Accounts Updated", description=f"Successfully updated {updated_count} out of {len(accounts)} accounts.")
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AccountCog(bot))