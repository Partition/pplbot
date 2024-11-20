from imghdr import tests
import math

from discord.ext import commands
from discord import app_commands
import discord
from models import Account
from models.invite import Invite
from utils.embed_gen import EmbedGenerator
from models.player import Player, PlayerDoesNotExist, PlayerAlreadyExists
from models.team import Team
from database import AsyncSessionLocal
from config import REGISTERED_ROLE, NICKNAME_CHARACTER_LIMIT, GUILD_ID
from random import choice
from utils.enums import LeagueRole, TeamLeague
from utils.util_funcs import get_discord_unix_timestamp_long, get_multi_opgg, get_opgg
from utils.paginator import ButtonPaginator
from utils.views import HelpView

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction: discord.Interaction):
        """Check the bot's latency.
        """
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Pong!", description=f"Latency: {latency}ms"))

    @app_commands.command()
    async def coinflip(self, interaction: discord.Interaction):
        """Toss a coin.
        """
        flip = ["heads", "tails"]
        result = choice(flip)
        await interaction.response.send_message(embed=EmbedGenerator.default_embed(title="Cling!", description=f"The result is **{result}**."))

    @app_commands.command()
    async def register(self, interaction: discord.Interaction, role: LeagueRole, nickname: str = ""):
        """Register to the database.
        
        Parameters:
        role: LeagueRole
            The role you play.
        nickname: str
            The nickname you want to be known as.
        """
        
        if len(nickname) > NICKNAME_CHARACTER_LIMIT:
               return await interaction.response.send_message(embed=EmbedGenerator.error_embed(
                        title="Registration Failed",
                        description=f"Your nickname cannot exceed 24 characters."
                    )
                )
        
        async with AsyncSessionLocal() as session:
            if await Player.exists(session, interaction.user.id):
               return await interaction.response.send_message(
                    embed=EmbedGenerator.error_embed(
                        title="Registration Failed",
                        description="You are already registered."
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
            oops_str = " (can't quite give you roles or change your nickname)"
        finally:
            await interaction.response.send_message(
                embed=EmbedGenerator.success_embed(
                title="Registration Successful",
                description=f"Welcome, {new_player.nickname}! You have been registered{oops_str if oops_str else ''}. "
                )
            )

    @app_commands.command()
    async def nick(self, interaction: discord.Interaction, nickname: str = ""):
        """Change your nickname.
        
        Parameters:
        nickname: str
            The nickname you want to change to.
        """
        async with AsyncSessionLocal() as session:
            if len(nickname) > NICKNAME_CHARACTER_LIMIT:
               return await interaction.response.send_message(
                    embed=EmbedGenerator.error_embed(
                        title="Nickname Update Failed",
                        description=f"Your nickname cannot exceed 24 characters."
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
            await interaction.response.send_message(
                embed=EmbedGenerator.error_embed(
                    title="Nickname Update Failed",
                    description="I don't have permission to change your nickname."
                )
            )
        finally:
            await interaction.response.send_message(
                embed=EmbedGenerator.success_embed(
                    title="Nickname Updated",
                    description=f"{f'Your nickname has been cleared' if not nickname else f'Your nickname has been changed to [{team_tag}]{nickname}'}"
                )
            )


    @app_commands.command()
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        """View a profile.
        
        Parameters:
        member: Optional[discord.Member]
            The member you want to view the profile of (defaults to yourself).
        """
        if not member:
            member = interaction.user
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, member.id)
            if not player:
                return await interaction.response.send_message(embed=EmbedGenerator.error_embed(
                    title=f"Profile - {member.name}",
                    description="This player is not registered."
                ))

            team = await Team.fetch_by_player_discord_id(session, player.discord_id)
            team_name = "None"
            team_tag = "None"
            captain_mention = "None"
            if team:
                team_name = team.name
                captain = await Player.fetch_from_discord_id(session, team.captain_id)
                captain_member = interaction.guild.get_member(captain.discord_id)
                captain_mention = captain_member.mention if captain_member else "None"
                team_tag = team.tag
                team_league = team.league

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
                        f"**Team League: ** {team_league}\n"
                        f"**Team Captain: ** {captain_mention}\n"
                        f"**Team Tag: ** {team_tag}\n")
        accounts_east_str_list = '\n'.join(f'[{x}]({get_opgg("euw", x)})' for x in accounts_east)
        accounts_west_str_list = '\n'.join(f'[{x}]({get_opgg("euw", x)})' for x in accounts_west)
        
        if accounts_east:
            embed.add_field(
                name="",
                value=f"**Europe East ([All]({get_multi_opgg('eune', accounts_east)}))**\n{accounts_east_str_list}",
                inline=True
            )
        if accounts_west:
            embed.add_field(
                name="",
                value=f"**Europe West ([All]({get_multi_opgg('euw', accounts_west)}))**\n{accounts_west_str_list}",
                inline=True
            )

        await interaction.response.send_message(embed=embed)
    
    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """View the help menu.
        """
        await interaction.response.send_message(view=HelpView(cogs=self.bot.cogs))

    @app_commands.command()
    async def invites(self, interaction: discord.Interaction):
        """View your active invites.
        """
        async with AsyncSessionLocal() as session:
            player = await Player.fetch_from_discord_id(session, interaction.user.id)
            if not player:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(
                    title="Registration Required",
                    description="You need to be registered to view your invites"))
                return
            
            active_invites = await Invite.fetch_active_invites_by_invitee(session, player.discord_id)
            if not active_invites:
                await interaction.response.send_message(embed=EmbedGenerator.error_embed(
                    title="No Active Invites",
                    description="You have no active invites"))
                return
            
        per_page = 5
        amount_of_pages = math.ceil(len(active_invites) / per_page)
        pages = [EmbedGenerator.default_embed(
                title=f"Active Invites - {player.nickname}", 
                description="\n".join([f"- <@{invite.team_id}> (Expires: {get_discord_unix_timestamp_long(invite.expires_at)})" for invite in active_invites[i*per_page:(i+1)*per_page]])) for i in range(amount_of_pages)]
        if amount_of_pages > 1:
            paginator = ButtonPaginator(pages)
            await paginator.start(interaction)
            return
        await interaction.response.send_message(embed=pages[0])
    
    # Some test commands for testing the bot
    @app_commands.command()
    async def team_check(self, interaction: discord.Interaction):
        """Check your team.
        """
        async with AsyncSessionLocal() as session:
            team = await Team.fetch_by_player_discord_id(session, interaction.user.id)
        await interaction.response.send_message(
            embed=EmbedGenerator.default_embed(
                title="Your Team",
                description=f"You are on the team {team.name}."
            )
        )
    
    @app_commands.command()
    async def testpaginator(self, interaction: discord.Interaction):
        """Test paginator.
        """
        # can iterate over Teams and create embeds for each team and append them to pages
        pages = [EmbedGenerator.default_embed(title=f"Team A", description=f"Members: aaaa."),
                 EmbedGenerator.default_embed(title=f"Team B", description=f"Members: bbbb.")]
        paginator = ButtonPaginator(pages)
        await paginator.start(interaction)
        
        
async def setup(bot):
    await bot.add_cog(General(bot), guilds=[discord.Object(id=GUILD_ID)])