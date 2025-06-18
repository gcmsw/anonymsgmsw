from discord.ext import commands
from discord import app_commands
import discord
import os

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.log_channel_id = int(os.environ.get("LOG_CHANNEL_ID"))
            self.commands_channel_id = int(os.environ.get("COMMANDS_CHANNEL_ID"))  # Original text channel
            self.forum_channel_id = int(os.environ.get("FORUM_CHANNEL_ID", 1384999875237646508))  # Forum channel
        except KeyError as e:
            raise RuntimeError(f"Missing required environment variable: {e}")

    @app_commands.command(name="sendanonymously", description="Send an anonymous site review to the forum")
    @app_commands.describe(site="The site name (used as the thread title)", review="Your anonymous review message")
    async def send_forum_review(self, interaction: discord.Interaction, site: str, review: str):
        if len(review) > 1900:
            await interaction.response.send_message("Your review exceeds the 1900 character limit.", ephemeral=True)
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        forum_channel = self.bot.get_channel(self.forum_channel_id)

        log_message = (
            f"Author: {interaction.user}\n"
            f"Author ID: {interaction.user.id}\n"
            f"Site: {site}\n"
            f"Content: {review}"
        )

        if log_channel:
            await log_channel.send(log_message)

        if isinstance(forum_channel, discord.ForumChannel):
            thread = await forum_channel.create_thread(name=site, content=review)
            await interaction.response.send_message(f"Your anonymous review has been posted to a new thread in the forum: **{site}**", ephemeral=True)
        else:
            await interaction.response.send_message("Forum channel not found or is not a forum channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
