import discord

class EmbedGenerator:
    @staticmethod
    def default_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )

    @staticmethod
    def success_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green()
        )

    @staticmethod
    def decline_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )

    @staticmethod
    def error_embed(title: str, description: str) -> discord.Embed:
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color.dark_red()
        )
