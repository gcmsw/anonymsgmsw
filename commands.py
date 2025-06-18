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
        name="sendanonymously",
        description="Send an anonymous site review (Admins will see your name in logs only)"
    )
    @app_commands.describe(
        site_name="Name of the site you're reviewing",
        message="Your review (up to 1900 characters)",
        rating="Star rating from 1 (worst) to 5 (best)"
    )
    async def sendmsg(self, interaction: discord.Interaction, site_name: str, message: str, rating: app_commands.Range[int, 1, 5]):
        if len(message) > 1900:
            await interaction.response.send_message("Your message exceeds the 1900 character limit.", ephemeral=True)
            return

        forum_channel = self.bot.get_channel(self.forum_channel_id)
        log_channel = self.bot.get_channel(self.log_channel_id)

        stars = "⭐" * rating
        post_content = f"{stars} - {message}"

        thread = await forum_channel.create_thread(name=site_name, content=post_content)

        log_msg = (
            f"[ANONYMOUS REVIEW]\nSite: {site_name}\nRating: {rating}\n"
            f"Author: {interaction.user}\nID: {interaction.user.id}\nMessage: {message}"
        )
        await log_channel.send(log_msg)

        await interaction.response.send_message("Your anonymous review has been submitted.", ephemeral=True)

    @app_commands.command(
        name="replyanon",
        description="Reply anonymously to a thread (as a question, answer, or additional review)"
    )
    @app_commands.describe(
        thread_id="Thread you want to reply in",
        reply_type="Choose type of reply",
        message="The content of your reply",
        rating="Optional rating (only if reply type is 'review')"
    )
    async def replyanon(self, interaction: discord.Interaction, thread_id: str, reply_type: str, message: str, rating: int = None):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        emoji = {
            "question": "↩️",  # ↩️
            "answer": "💬",   # 💬
            "review": "⭐" * rating if rating else "⭐"
        }.get(reply_type.lower(), "")

        content = f"{emoji} - {message}"

        if thread and isinstance(thread, discord.Thread):
            await thread.send(content)
            log_msg = (
                f"[ANONYMOUS {reply_type.upper()} REPLY]\nThread ID: {thread_id}\n"
                f"Author: {interaction.user}\nID: {interaction.user.id}\nMessage: {message}\nRating: {rating}"
            )
            await log_channel.send(log_msg)
            await interaction.response.send_message("Your anonymous reply was posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @replyanon.autocomplete("thread_id")
    async def thread_id_autocomplete(self, interaction: discord.Interaction, current: str):
        forum_channel = self.bot.get_channel(self.forum_channel_id)
        if not isinstance(forum_channel, discord.ForumChannel):
            return []
        return [
            app_commands.Choice(name=thread.name, value=str(thread.id))
            for thread in forum_channel.threads
            if current.lower() in thread.name.lower()
        ][:25]  # limit to top 25 results

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
