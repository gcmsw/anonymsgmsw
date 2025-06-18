from discord.ext import commands
from discord import app_commands
import discord
import os

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.log_channel_id = int(os.environ["LOG_CHANNEL_ID"])  # Staff-only log
            self.commands_channel_id = int(os.environ["COMMANDS_CHANNEL_ID"])  # Anonymous message destination
            self.forum_channel_id = int(os.environ["FORUM_CHANNEL_ID"])  # Forum channel for anonymous replies
        except KeyError as e:
            raise RuntimeError(f"Missing required environment variable: {e}")

    @app_commands.command(name="sendanonymously", description="Send an anonymous message (Only staff will see your name)")
    @app_commands.describe(site="The site name (will be used as the thread title)", message="Your anonymous review message")
    async def sendanonymously(self, interaction: discord.Interaction, site: str, message: str):
        if len(message) > 1900:
            await interaction.response.send_message("Your message exceeds the 1900 character limit.", ephemeral=True)
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        forum_channel = self.bot.get_channel(self.forum_channel_id)

        if not forum_channel or not isinstance(forum_channel, discord.ForumChannel):
            await interaction.response.send_message("Forum channel not found or incorrect type.", ephemeral=True)
            return

        thread = await forum_channel.create_thread(name=site, content=message)

        if log_channel:
            await log_channel.send(
                f"[ANONYMOUS POST]\nAuthor: {interaction.user} ({interaction.user.id})\nSite: {site}\nContent: {message}"
            )

        await interaction.response.send_message("✅ Your anonymous post has been submitted.", ephemeral=True)

    @app_commands.command(name="replyanon", description="Reply anonymously to an existing forum thread.")
    @app_commands.describe(thread_id="The ID of the forum thread", message="The reply you want to send")
    async def replyanon(self, interaction: discord.Interaction, thread_id: str, message: str):
        if len(message) > 1900:
            await interaction.response.send_message("Your message exceeds the 1900 character limit.", ephemeral=True)
            return

        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if not isinstance(thread, discord.Thread):
            await interaction.response.send_message("❌ Invalid thread ID. Please make sure it's from the forum.", ephemeral=True)
            return

        await thread.send(message)

        if log_channel:
            await log_channel.send(
                f"[ANONYMOUS REPLY]\nAuthor: {interaction.user} ({interaction.user.id})\nThread ID: {thread_id}\nMessage: {message}"
            )

        await interaction.response.send_message("✅ Your anonymous reply has been sent.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
