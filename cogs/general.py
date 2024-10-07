from imghdr import tests

from discord.ext import commands
from discord import app_commands
import discord
from models import Account
from utils.embed_gen import EmbedGenerator
from models.player import Player, PlayerDoesNotExist, PlayerAlreadyExists
from models.team import Team
from database import AsyncSessionLocal
from config import REGISTERED_ROLE, NICKNAME_CHARACTER_LIMIT
from random import choice
from utils.enums import LeagueRole
from utils.util_funcs import get_multi_opgg, get_opgg
from utils.paginator import ButtonPaginator

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check the bot's latency")
    @app_commands.guilds(911940380717617202)
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Pong!", description=f"Latency: {latency}ms"))

    @app_commands.command(name="coinflip", description="Toss a coin")
    @app_commands.guilds(911940380717617202)
    async def coinflip(self, interaction: discord.Interaction):
        flip = ["heads", "tails"]
        result = choice(flip)
        await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Cling!", description=f"The result is **{result}**"))

    @app_commands.command(name="register", description="Register to the database")
    @app_commands.describe(role="The role of the player", nickname="The nickname of the player")
    @app_commands.guilds(911940380717617202)
    async def register(self, interaction: discord.Interaction, role: LeagueRole, nickname: str = ""):
        async with AsyncSessionLocal() as session:
            if await Player.exists(session, interaction.user.id):
               return await interaction.response.send_message(
                    embed=EmbedGenerator.error_embed(
                        title="Registration Failed",
                        description="You are already registered"
                    )
                )

            if len(nickname) > NICKNAME_CHARACTER_LIMIT:
               return await interaction.response.send_message(
                    embed=EmbedGenerator.error_embed(
                        title="Registration Failed",
                        description=f"Your nickname cannot exceed 24 characters"
                    )
                )
            new_player = await Player.create(
                session,
                discord_id=interaction.user.id,
                role=role.value,
                nickname=interaction.user.nick if not nickname else nickname
            )
            await session.commit()
        try:
            league_role = discord.utils.get(interaction.guild.roles, name=role.value)
            await interaction.user.add_roles(discord.Object(id=REGISTERED_ROLE), league_role)
            if nickname:
                await interaction.user.edit(nick=nickname)

        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=EmbedGenerator.error_embed(
                    title="kill yourself",
                    description=f"Welcome, {new_player.nickname}! faggot."
                )
            )

        await interaction.response.send_message(
            embed=EmbedGenerator.success_embed(
                title="Registration Successful",
                description=f"Welcome, {new_player.nickname}! You have been registered."
            )
        )

    @app_commands.command(name="nick", description="Change your nickname")
    @app_commands.guilds(911940380717617202)
    async def nick(self, interaction: discord.Interaction, nickname: str = ""):
        async with AsyncSessionLocal() as session:
            if len(nickname) > NICKNAME_CHARACTER_LIMIT:
               return await interaction.response.send_message(
                    embed=EmbedGenerator.error_embed(
                        title="Registration Failed",
                        description=f"Your nickname cannot exceed 24 characters"
                    )
                )
            
            team = await Team.fetch_by_player_discord_id(session, interaction.user.id)
            team_tag = f"[{team.tag}] " if team else ""
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            player.nickname = nickname
            await session.commit()

        try:
            await interaction.user.edit(nick=f"{team_tag}{nickname if nickname else interaction.user.name}")
        except discord.Forbidden:
            pass

        if nickname == "":
            await interaction.response.send_message(
                embed=EmbedGenerator.default_embed(
                    title="Nickname Cleared",
                    description=f"Your nickname has been cleared"
                )
            )

        else:
            await interaction.response.send_message(
                embed=EmbedGenerator.default_embed(
                    title="Nickname Changed",
                    description=f"Your nickname is now **{team_tag}{nickname}**"
                )
            )

    @app_commands.command(name="team_check", description="Check your team")
    @app_commands.guilds(911940380717617202)
    async def team_check(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            team = await Team.fetch_by_player_discord_id(session, interaction.user.id)
        await interaction.response.send_message(
            embed=EmbedGenerator.default_embed(
                title="Your Team",
                description=f"You are on the team {team.name}."
            )
        )

    @app_commands.command(name="profile", description="View a profile")
    @app_commands.guilds(911940380717617202)
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member=interaction.user
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, member.id)
            if not player:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(
                    title=f"Profile - {member.name}",description="This player is not registered"))

            team = await Team.fetch_by_player_discord_id(session, player.discord_id)
            team_name = "None"
            team_tag = "None"
            captain_mention = "None"
            if team:
                team_name = team.name
                captain = await Player.fetch_from_discord_id(session, team.captain_id)
                captain_member = interaction.guild.get_member(captain.discord_id)
                captain_mention = captain_member.mention
                team_tag = team.tag

            account_info = await Account.fetch_all_from_player_id(session, member.id)
            accounts_east = list()
            accounts_west = list()
            for account in account_info:
                if account.server == "EUNE":
                    accounts_east.append(str(account))
                else:
                    accounts_west.append(str(account))

        embed = EmbedGenerator.default_embed(
            title=f"Profile - {member.name}",
            description=f"**Discord: ** {member.mention}\n"
                        f"**Role: ** {player.role}\n\n"
                        f"**Team: ** {team_name}\n"
                        f"**Team Captain: ** {captain_mention}\n"
                        f"**Team Tag: ** {team_tag}\n")
        if accounts_east:
            embed.add_field(name="",value=f"**Europe East ([All]({get_multi_opgg("eune",accounts_east)}))**\n"\
                                     f"{"\n".join(f"[{x}]({get_opgg("eune", x)})" for x in accounts_east)}", inline=True)
        if accounts_west:
            embed.add_field(name="",value=f"**Europe West ([All]({get_multi_opgg("euw",accounts_west)}))**\n"\
                                     f"{"\n".join(f"[{x}]({get_opgg("euw", x)})" for x in accounts_west)}", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="testpaginator", description="Test paginator")
    @app_commands.guilds(911940380717617202)
    async def testpaginator(self, interaction: discord.Interaction):
        
        # can iterate over Teams and create embeds for each team and append them to pages
        pages = [EmbedGenerator.default_embed(title=f"Team A", description=f"Members: aaaa."),
                 EmbedGenerator.default_embed(title=f"Team B", description=f"Members: bbbb.")]
        paginator = ButtonPaginator(pages)
        await paginator.start(interaction)
        

async def setup(bot):
    await bot.add_cog(General(bot))