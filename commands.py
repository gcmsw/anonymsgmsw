from discord.ext import commands
from discord import app_commands
import discord
import os

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1382563380367331429  # Log channel
        self.forum_channel_id = 1384999875237646508  # Forum channel

    @app_commands.command(
        name="anon-newsite",
        description="Create a new anonymous review thread. Use /anon-addreview if the site already exists."
    )
    @app_commands.describe(
        site_name="Name of the site you're reviewing",
        message="Your review (up to 1900 characters)",
        rating="Star rating from 1 (worst) to 5 (best)"
    )
    async def anon_newsite(self, interaction: discord.Interaction, site_name: str, message: str, rating: app_commands.Range[int, 1, 5]):
        forum_channel = self.bot.get_channel(self.forum_channel_id)
        log_channel = self.bot.get_channel(self.log_channel_id)

        existing = [t.name.lower() for t in forum_channel.threads]
        if site_name.lower() in existing:
            await interaction.response.send_message("That site already has a post. Please use /anon-addreview instead.", ephemeral=True)
            return

        stars = "⭐" * rating
        post_content = f"{stars} - {message}"

        thread = await forum_channel.create_thread(name=site_name, content=post_content)

        log_msg = (
            f"[NEW SITE REVIEW]\nSite: {site_name}\nRating: {rating}\n"
            f"Author: {interaction.user} ({interaction.user.id})\n"
            f"Content: {message}\nThread Link: https://discord.com/channels/{interaction.guild.id}/{thread.id}"
        )
        await log_channel.send(log_msg)
        await interaction.response.send_message("Your anonymous review thread has been created.", ephemeral=True)

    @app_commands.command(
        name="anon-addreview",
        description="Add an anonymous review to an existing site thread."
    )
    @app_commands.describe(
        thread_id="The thread for the site",
        message="Your review (up to 1900 characters)",
        rating="Star rating from 1 (worst) to 5 (best)"
    )
    async def anon_addreview(self, interaction: discord.Interaction, thread_id: str, message: str, rating: app_commands.Range[int, 1, 5]):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        stars = "⭐" * rating
        content = f"{stars} - {message}"

        if isinstance(thread, discord.Thread):
            sent_msg = await thread.send(content)
            log_msg = (
                f"[REVIEW]\nThread ID: {thread_id}\nRating: {rating}\n"
                f"Author: {interaction.user} ({interaction.user.id})\n"
                f"Content: {message}\nMessage Link: https://discord.com/channels/{interaction.guild.id}/{thread.id}/{sent_msg.id}"
            )
            await log_channel.send(log_msg)
            await interaction.response.send_message("Your anonymous review was posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Thread not found.", ephemeral=True)

    @app_commands.command(
        name="anon-question",
        description="Ask a question anonymously in a thread."
    )
    @app_commands.describe(
        thread_id="Thread to ask in",
        reference_msg_id="Optional: message to reply to",
        message="Your question"
    )
    async def anon_question(self, interaction: discord.Interaction, thread_id: str, message: str, reference_msg_id: str = None):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if isinstance(thread, discord.Thread):
            ref = None
            if reference_msg_id:
                try:
                    ref = await thread.fetch_message(int(reference_msg_id))
                except:
                    pass
            sent_msg = await thread.send("❓ - " + message, reference=ref)
            log_msg = (
                f"[QUESTION]\nThread ID: {thread_id}\nAuthor: {interaction.user} ({interaction.user.id})\n"
                f"Content: {message}\nMessage Link: https://discord.com/channels/{interaction.guild.id}/{thread.id}/{sent_msg.id}"
            )
            await log_channel.send(log_msg)
            await interaction.response.send_message("Question posted anonymously.", ephemeral=True)
        else:
            await interaction.response.send_message("Thread not found.", ephemeral=True)

    @app_commands.command(
        name="anon-reply",
        description="Reply anonymously in a thread."
    )
    @app_commands.describe(
        thread_id="Thread to reply in",
        reference_msg_id="Optional: message to reply to",
        message="Your reply"
    )
    async def anon_reply(self, interaction: discord.Interaction, thread_id: str, message: str, reference_msg_id: str = None):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if isinstance(thread, discord.Thread):
            ref = None
            if reference_msg_id:
                try:
                    ref = await thread.fetch_message(int(reference_msg_id))
                except:
                    pass
            sent_msg = await thread.send("↩️ - " + message, reference=ref)
            log_msg = (
                f"[REPLY]\nThread ID: {thread_id}\nAuthor: {interaction.user} ({interaction.user.id})\n"
                f"Content: {message}\nMessage Link: https://discord.com/channels/{interaction.guild.id}/{thread.id}/{sent_msg.id}"
            )
            await log_channel.send(log_msg)
            await interaction.response.send_message("Reply posted anonymously.", ephemeral=True)
        else:
            await interaction.response.send_message("Thread not found.", ephemeral=True)

    @anon_addreview.autocomplete("thread_id")
    @anon_question.autocomplete("thread_id")
    @anon_reply.autocomplete("thread_id")
    async def thread_autocomplete(self, interaction: discord.Interaction, current: str):
        forum_channel = self.bot.get_channel(self.forum_channel_id)
        if not isinstance(forum_channel, discord.ForumChannel):
            return []
        return [
            app_commands.Choice(name=thread.name, value=str(thread.id))
            for thread in forum_channel.threads
            if current.lower() in thread.name.lower()
        ][:25]

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
