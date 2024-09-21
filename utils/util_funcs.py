from pulsefire.clients import RiotAPIClient
import os
from dotenv import load_dotenv

load_dotenv(override=True)

async def get_account_info(username: str, tag: str, region: str):
        async with RiotAPIClient(default_headers={"X-Riot-Token": os.getenv("RIOT_API_KEY")}) as client:
            account = await client.get_account_v1_by_riot_id(region="europe", game_name=username, tag_line=tag)
            summoner = await client.get_lol_summoner_v4_by_puuid(region=region, puuid=account["puuid"])
            return account, summoner