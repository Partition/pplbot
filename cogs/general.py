from code import interact
from dis import disco
from enum import nonmember
from logging import captureWarnings
from math import trunc

from discord.ext import commands
from discord import app_commands
import discord
from utils.embed_gen import EmbedGenerator
from models.player import Player, PlayerDoesNotExist
from models.team import Team
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal
from config import LANE_ROLES
from random import choice
from models.team import Team

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
        if interaction.user.id == 308587420713091073:
           result = flip[0]
        await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Cling!", description=f"The result is **{result}**"))

    @app_commands.command(name="roles", description="List the available server roles")
    @app_commands.guilds(911940380717617202)
    async def roles(self, interaction: discord.Interaction):
        unsorted_roles = list(interaction.guild.roles)
        role_names = list()
        for item in unsorted_roles:
            role_names.append(item.name)
        role_names.sort()
        role_list = "\n".join(role_names)
        await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Roles", description=f"{role_list}"))

    @app_commands.command(name="randrole", description="go crazy go stupid")
    @app_commands.guilds(911940380717617202)
    async def randrole(self, interaction: discord.Interaction):
        lolrole = choice(interaction.guild.roles)
        print(lolrole)
        await interaction.user.add_roles(lolrole, atomic = True)
        await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Poof!", description=f"You are now **{lolrole}**"))

    @app_commands.command(name="register", description="Register to the database")
    @app_commands.guilds(911940380717617202)
    async def register(self, interaction: discord.Interaction):
        member_roles = [role.name for role in interaction.user.roles]
        lane_role = list(filter(lambda x: x in LANE_ROLES, member_roles))
        
        if not lane_role:
            await interaction.response.send_message(
                embed=EmbedGenerator.error_embed(
                    title="Registration Failed",
                    description="You must have a lane role to register."
                )
            )
            return
        
        async with AsyncSessionLocal() as session:
            # Create a new player
            new_player = await Player.create(
                session,
                discord_id=interaction.user.id,
                role=lane_role[0]
            )
            session.commit()
       
        
        await interaction.response.send_message(
            embed=EmbedGenerator.success_embed(
                title="Registration Successful",
                description=f"Welcome, {interaction.user.name}! You have been registered."
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

async def setup(bot):
    await bot.add_cog(General(bot))


    @app_commands.command(name="profile", description="View a profile")
    @app_commands.guilds(911940380717617202)
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        if member is None:
            member=interaction.user
        async with AsyncSessionLocal() as session:
            try:
                player = await Player.fetch_from_discord_id(session, interaction.user.id)
                player_role = player.role
            except PlayerDoesNotExist:
                player_role = "None"

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

        await interaction.response.send_message(
            embed = EmbedGenerator.default_embed(
                title=f"Profile - {member.name}",
                description=f"**Discord: ** {member.mention}\n"
                            f"**Role: ** {player_role}\n\n"
                            f"**Team: ** {team_name}\n"
                            f"**Team Captain: ** {captain_mention}\n"
                            f"**Team Tag: ** {team_tag}\n"
                            f"**Accounts: **"
            )
        )


