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
        description="Submit a new anonymous review for a site (includes 1-5 star rating)"
    )
    @app_commands.describe(
        site_name="Name of the site",
        message="Your review (up to 1900 characters)",
        rating="Star rating from 1 (worst) to 5 (best)"
    )
    async def newsite(self, interaction: discord.Interaction, site_name: str, message: str, rating: app_commands.Range[int, 1, 5]):
        forum_channel = self.bot.get_channel(self.forum_channel_id)
        log_channel = self.bot.get_channel(self.log_channel_id)

        stars = "⭐" * rating
        post_content = f"{stars} - {message}"

        # Check for duplicate thread
        for thread in forum_channel.threads:
            if thread.name.strip().lower() == site_name.strip().lower():
                sent_msg = await thread.send(post_content)
                await log_channel.send(
                    f"[ANON REDIRECTED REVIEW]\nSite: {site_name}\nRating: {rating}\nAuthor: {interaction.user}\nMessage: {message}\nThread: {sent_msg.jump_url}"
                )
                try:
                    await interaction.response.send_message(
                        f"Looks like that site already has a post. I've posted your review to the existing thread here: {thread.mention}",
                        ephemeral=True
                    )
                except discord.NotFound:
                    pass
                return

        thread = await forum_channel.create_thread(name=site_name, content=post_content)
        await log_channel.send(
            f"[ANON NEW THREAD]\nSite: {site_name}\nRating: {rating}\nAuthor: {interaction.user}\nMessage: {message}\nThread: {thread.jump_url}"
        )
        await interaction.response.send_message("Your anonymous review has been submitted.", ephemeral=True)

    @app_commands.command(name="anon-addreview", description="Add a review to an existing site thread")
    @app_commands.describe(thread_id="Thread to post in", message="Your review", rating="Star rating 1-5")
    async def addreview(self, interaction: discord.Interaction, thread_id: str, message: str, rating: app_commands.Range[int, 1, 5]):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if thread and isinstance(thread, discord.Thread):
            stars = "⭐" * rating
            sent_msg = await thread.send(f"{stars} - {message}")
            await log_channel.send(
                f"[ANON ADD REVIEW]\nThread: {thread.name}\nRating: {rating}\nAuthor: {interaction.user}\nMessage: {message}\nMessage: {sent_msg.jump_url}"
            )
            await interaction.response.send_message("Your anonymous review was posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @app_commands.command(name="anon-question", description="Ask a question anonymously in a thread")
    @app_commands.describe(thread_id="Thread to ask in", message="Your question")
    async def anon_question(self, interaction: discord.Interaction, thread_id: str, message: str):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if thread and isinstance(thread, discord.Thread):
            sent_msg = await thread.send(f"❓ - {message}")
            await log_channel.send(
                f"[ANON QUESTION]\nThread: {thread.name}\nAuthor: {interaction.user}\nMessage: {message}\nMessage: {sent_msg.jump_url}"
            )
            await interaction.response.send_message("Your anonymous question was posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @app_commands.command(name="anon-reply", description="Reply anonymously in a thread to a message")
    @app_commands.describe(thread_id="Thread to reply in", message_id="ID of the message to reply to", message="Your reply")
    async def anon_reply(self, interaction: discord.Interaction, thread_id: str, message_id: str, message: str):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if thread and isinstance(thread, discord.Thread):
            try:
                reference_msg = await thread.fetch_message(int(message_id))
                sent_msg = await thread.send(f"↩️ - {message}", reference=reference_msg)
                await log_channel.send(
                    f"[ANON REPLY]\nThread: {thread.name}\nAuthor: {interaction.user}\nMessage: {message}\nMessage: {sent_msg.jump_url}"
                )
                await interaction.response.send_message("Your anonymous reply was posted.", ephemeral=True)
            except discord.NotFound:
                await interaction.response.send_message("Could not find that message in the thread.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @addreview.autocomplete("thread_id")
    @anon_question.autocomplete("thread_id")
    @anon_reply.autocomplete("thread_id")
    async def thread_id_autocomplete(self, interaction: discord.Interaction, current: str):
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
