import discord
from discord.ext import commands
from config import REGISTERED_ROLE
from models.player import Player, PlayerNotInTeam
from models.team import Team
from database import AsyncSessionLocal

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, payload.user.id)
            if player:
                try:
                    if await player.is_captain:
                        team = await Team.fetch_from_id(session, player.team_id)
                        if team:
                            team.captain_id = None
                    await player.remove_from_team(session, player.team_id)
                    await session.commit()
                except PlayerNotInTeam:
                    return

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, member.id)
            if not player:
                return
            member = await self.bot.get_member(player.discord_id)
            if member:
                await member.add_roles(discord.Object(role_id=REGISTERED_ROLE))
                await member.edit(nick=player.nickname)
            await session.commit()
                

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
