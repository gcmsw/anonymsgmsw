from discord.ext import commands
from discord import app_commands
import discord
import os

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1382563380367331429
        self.forum_channel_id = 1384999875237646508

    @app_commands.command(
        name="anon-newsite",
        description="Submit a new anonymous site review (will create a post unless one exists)"
    )
    @app_commands.describe(
        site_name="Name of the site you're reviewing",
        message="Your review (up to 1900 characters)",
        rating="Star rating from 1 (worst) to 5 (best)"
    )
    async def newsite(self, interaction: discord.Interaction, site_name: str, message: str, rating: app_commands.Range[int, 1, 5]):
        if len(message) > 1900:
            await interaction.response.send_message("Your message exceeds the 1900 character limit.", ephemeral=True)
            return

        forum_channel = self.bot.get_channel(self.forum_channel_id)
        log_channel = self.bot.get_channel(self.log_channel_id)
        
        existing_thread = discord.utils.find(lambda t: t.name.lower() == site_name.lower(), forum_channel.threads)
        stars = "⭐" * rating
        post_content = f"{stars} - {message}"

        if existing_thread:
            response = await existing_thread.send(post_content)
            thread_url = f"https://discord.com/channels/{interaction.guild_id}/{existing_thread.id}/{response.id}"
            await interaction.response.send_message(f"That site already exists! Your review was posted here: {existing_thread.mention}", ephemeral=True)
        else:
            thread = await forum_channel.create_thread(name=site_name, content=post_content)
            thread_url = f"https://discord.com/channels/{interaction.guild_id}/{thread.id}"
            await interaction.response.send_message("Your anonymous review has been submitted.", ephemeral=True)

        log_msg = (
            f"[ANONYMOUS REVIEW]\nSite: {site_name}\nRating: {rating}\n"
            f"Author: {interaction.user}\nID: {interaction.user.id}\nMessage: {message}\nLink: {thread_url}"
        )
        await log_channel.send(log_msg)

    @app_commands.command(
        name="anon-addreview",
        description="Add another review to an existing site post"
    )
    @app_commands.describe(
        thread_id="Thread to post your review in",
        message="Your review (up to 1900 characters)",
        rating="Star rating from 1 (worst) to 5 (best)"
    )
    async def addreview(self, interaction: discord.Interaction, thread_id: str, message: str, rating: app_commands.Range[int, 1, 5]):
        thread = self.bot.get_channel(int(thread_id))
        if not isinstance(thread, discord.Thread):
            await interaction.response.send_message("Thread not found.", ephemeral=True)
            return

        stars = "⭐" * rating
        content = f"{stars} - {message}"
        response = await thread.send(content)

        log_channel = self.bot.get_channel(self.log_channel_id)
        msg_url = f"https://discord.com/channels/{interaction.guild_id}/{thread.id}/{response.id}"
        log_msg = (
            f"[ADDITIONAL REVIEW]\nThread ID: {thread_id}\nRating: {rating}\n"
            f"Author: {interaction.user}\nMessage: {message}\nLink: {msg_url}"
        )
        await log_channel.send(log_msg)

        await interaction.response.send_message("Your anonymous review was added.", ephemeral=True)

    @app_commands.command(
        name="anon-question",
        description="Ask a question anonymously in a review thread"
    )
    @app_commands.describe(
        thread_id="Thread to ask your question in",
        message="Your question (up to 1900 characters)"
    )
    async def question(self, interaction: discord.Interaction, thread_id: str, message: str):
        await self._post_anon(interaction, thread_id, message, label="❓", tag="QUESTION")

    @app_commands.command(
        name="anon-reply",
        description="Reply anonymously to a review thread"
    )
    @app_commands.describe(
        thread_id="Thread to reply in",
        message="Your response (up to 1900 characters)"
    )
    async def reply(self, interaction: discord.Interaction, thread_id: str, message: str):
        await self._post_anon(interaction, thread_id, message, label="↩️", tag="REPLY")

    async def _post_anon(self, interaction, thread_id, message, label, tag):
        thread = self.bot.get_channel(int(thread_id))
        if not isinstance(thread, discord.Thread):
            await interaction.response.send_message("Thread not found.", ephemeral=True)
            return

        response = await thread.send(f"{label} - {message}")

        msg_url = f"https://discord.com/channels/{interaction.guild_id}/{thread.id}/{response.id}"
        log_channel = self.bot.get_channel(self.log_channel_id)
        await log_channel.send(
            f"[ANONYMOUS {tag}]\nThread ID: {thread_id}\nAuthor: {interaction.user}\n"
            f"Message: {message}\nLink: {msg_url}"
        )
        await interaction.response.send_message("Your anonymous message has been posted.", ephemeral=True)

    @addreview.autocomplete("thread_id")
    @question.autocomplete("thread_id")
    @reply.autocomplete("thread_id")
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
