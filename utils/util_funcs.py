from pulsefire.clients import RiotAPIClient
from dotenv import load_dotenv
from models.player import Player, PlayerAlreadyInTeam, PlayerNotInTeam
from models.team import Team
from sqlalchemy.ext.asyncio import AsyncSession
import os
import discord

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


async def player_join_team(session: AsyncSession, guild: discord.Guild, player: Player, team: Team):
    await player.add_to_team(session, team.id)
    
    member = await guild.get_member(player.discord_id)
    if not member:
        return False
    
    await member.add_roles(discord.utils.get(guild.roles, name=team.name))
    await member.edit(nick=f"[{team.tag}] {member.display_name}")
    return True

async def player_leave_team(session: AsyncSession, guild: discord.Guild, player: Player, team: Team):
    await player.remove_from_team(session, team.id)
    
    member = await guild.get_member(player.discord_id)
    if not member:
        return False
    
    await member.remove_roles(discord.utils.get(guild.roles, name=team.name))
    await member.edit(nick=None)
    return True