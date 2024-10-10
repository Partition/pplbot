from time import time
from pulsefire.clients import RiotAPIClient
from dotenv import load_dotenv
from config import TRANSFER_CHANNEL
from models.player import Player, PlayerAlreadyInTeam, PlayerNotInTeam
from models.team import Team
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import os
import discord
import datetime
from models.transfer import Transfer
from utils.enums import TransferType

load_dotenv(override=True)

async def get_account_info(username: str, tag: str, region: str):
        async with RiotAPIClient(default_headers={"X-Riot-Token": os.getenv("RIOT_API_KEY")}) as client:
            account = await client.get_account_v1_by_riot_id(region="europe", game_name=username, tag_line=tag)
            summoner = await client.get_lol_summoner_v4_by_puuid(region=region, puuid=account["puuid"])
            ranked = await client.get_lol_league_v4_entries_by_summoner(region=region, summoner_id=summoner["id"])
            return account, summoner, get_solo_queue_data(ranked)


def get_solo_queue_data(ranked_data):
    try:
        return next(entry for entry in ranked_data if entry['queueType'] == 'RANKED_SOLO_5x5')
    except StopIteration:
        return None
    
async def get_account_info_from_puuid(puuid: str, server: str):
    async with RiotAPIClient(default_headers={"X-Riot-Token": os.getenv("RIOT_API_KEY")}) as client:
        account = await client.get_account_v1_by_puuid(region="europe", puuid=puuid)
        summoner = await client.get_lol_summoner_v4_by_puuid(region=server, puuid=puuid)
        ranked = await client.get_lol_league_v4_entries_by_summoner(region=server, summoner_id=summoner["id"])
        return account, summoner, get_solo_queue_data(ranked)

# Player joins team (transfer_type = 1 PLAYER JOIN, or 3 TEAM CREATE)
async def player_join_team(session: AsyncSession, interaction: discord.Interaction, player: Player, team: Team, transfer_type: TransferType = TransferType.PLAYER_JOIN):
    try:
        await player.add_to_team(session, team.id)
        await send_transfer_message(session, interaction, player, team, transfer_type)
        await session.commit()
    except (PlayerAlreadyInTeam, SQLAlchemyError) as e:
        await session.rollback()
        return False, f"Database error: {str(e)}"

    member = interaction.guild.get_member(player.discord_id)
    if not member:
        return True, "Database updated, but member not found in the server"
    
    try:    
        await member.add_roles(discord.utils.get(interaction.guild.roles, name=team.name))
        await member.edit(nick=f"[{team.tag}] {player.nickname}")
        return True, "Player successfully joined the team"
    except discord.Forbidden:
        return True, "Database updated, but bot lacks permissions to add roles or edit nickname"
    except discord.HTTPException as e:
        return True, f"Database updated, but Discord API error: {str(e)}"

# Player leaves team (transfer_type = 2 PLAYER LEAVE, or 4 TEAM DISBAND)
async def player_leave_team(session: AsyncSession, interaction: discord.Interaction, player: Player, team: Team, transfer_type: TransferType = TransferType.PLAYER_LEAVE):
    try:
        await player.remove_from_team(session, team.id)
        await send_transfer_message(session, interaction, player, team, transfer_type)
        await session.commit()
    except (PlayerNotInTeam, SQLAlchemyError) as e:
        await session.rollback()
        return False, str(e)

    member = interaction.guild.get_member(player.discord_id)
    if not member:
        return True, "Database updated, but member not found in the server"
    
    try:
        await member.remove_roles(discord.utils.get(interaction.guild.roles, name=team.name))
        await member.edit(nick=None)
        return True, "Player successfully left the team"
    except discord.Forbidden:
        return True, "Database updated, but bot lacks permissions to remove roles or edit nickname"
    except discord.HTTPException as e:
        return True, f"Database updated, but Discord API error: {str(e)}"
    
async def send_transfer_message(session: AsyncSession, interaction: discord.Interaction, player: Player, team: Team, transfer_type: TransferType):
    transfer_channel = interaction.guild.get_channel(TRANSFER_CHANNEL)
    member = interaction.guild.get_member(player.discord_id)
    if not member:
        user = await interaction.client.fetch_user(player.discord_id)
        mention = f"**{user.display_name}**"
    else:
        mention = member.mention
        
    if transfer_type == TransferType.PLAYER_LEAVE:
        message = f"🔴 {mention} left **{team.name}** <t:{int(time())}:f>"
    elif transfer_type == TransferType.TEAM_DISBAND:
        message = f"🔴 {mention} left **{team.name}** because the team was disbanded <t:{int(time())}:f>"
    elif transfer_type == TransferType.PLAYER_JOIN:
        message = f"🟢 {mention} joined **{team.name}** <t:{int(time())}:f>"
    elif transfer_type == TransferType.TEAM_CREATE:
        message = f"🟢 {mention} created **{team.name}** <t:{int(time())}:f>"
        
    await Transfer.create(session, player.discord_id, team.id, transfer_type.value, player.role)
    await transfer_channel.send(message)
    
def get_multi_opgg(server: str, display_names: list):
    multi_opgg_link = list()
    for display_name in display_names:
         multi_opgg_link.append(display_name.replace(" ","+").replace("#","%23"))
    return f"https://www.op.gg/multisearch/{server}?summoners={"%2C".join(multi_opgg_link)}"

def get_opgg(server: str, display_name: str):
    return f"https://www.op.gg/summoners/{server}/{display_name.replace(" ", "+").replace("#","-")}"

def get_discord_unix_timestamp_long(datetime_obj: datetime.datetime): # 15 October 2024 00:51
    return f"<t:{int(datetime_obj.timestamp())}:f>"

def get_discord_unix_timestamp_short(datetime_obj: datetime.datetime): # 15/10/2024
    return f"<t:{int(datetime_obj.timestamp())}:d>"