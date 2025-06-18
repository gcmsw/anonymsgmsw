from discord.ext import commands
from discord import app_commands
import discord
import os

# Temporary in-memory store to track OPs by thread ID
original_posters = {}

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(os.environ.get("LOG_CHANNEL_ID"))
        self.commands_channel_id = int(os.environ.get("COMMANDS_CHANNEL_ID"))
        self.review_forum_id = int(os.environ.get("REVIEW_FORUM_CHANNEL_ID"))

    # --------------- Autocomplete for Threads ---------------
    async def autocomplete_thread_titles(self, interaction: discord.Interaction, current: str):
        forum = self.bot.get_channel(self.review_forum_id)
        if not forum:
            return []
        return [app_commands.Choice(name=thread.name[:100], value=str(thread.id))
                for thread in forum.threads if current.lower() in thread.name.lower()][:25]

    # --------------- /sendanonymously Command ---------------
    @app_commands.command(name="sendanonymously", description="Post an anonymous site review")
    @app_commands.describe(site_name="Field site name", message="Your anonymous review", rating="1 to 5 star rating")
    async def sendmsg(self, interaction: discord.Interaction, site_name: str, message: str, rating: app_commands.Range[int, 1, 5]):
        forum = self.bot.get_channel(self.review_forum_id)
        if not forum:
            await interaction.response.send_message("Forum channel not found.", ephemeral=True)
            return

        stars = "⭐" * rating
        thread = await forum.create_thread(name=site_name, content=f"{stars} - {message}")

        original_posters[thread.id] = interaction.user.id

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(
                f"[OP Review]\nAuthor: {interaction.user}\nSite: {site_name}\nRating: {rating}\nContent: {message}"
            )

        await interaction.response.send_message("Your review was posted anonymously.", ephemeral=True)

    # --------------- /replyanon Command ---------------
    @app_commands.command(name="replyanon", description="Post an anonymous reply in a forum thread")
    @app_commands.describe(thread_id="Select the thread", reply_type="Choose reply type", message="Your reply")
    @app_commands.choices(reply_type=[
        app_commands.Choice(name="Question", value="question"),
        app_commands.Choice(name="Answer", value="answer"),
        app_commands.Choice(name="Add Review", value="review")
    ])
    async def replyanon(self, interaction: discord.Interaction, 
                        thread_id: app_commands.Transform[str, autocomplete_thread_titles], 
                        reply_type: app_commands.Choice[str], 
                        message: str,
                        rating: app_commands.Range[int, 1, 5] = None):

        thread = self.bot.get_channel(int(thread_id))
        if not thread:
            await interaction.response.send_message("Thread not found.", ephemeral=True)
            return

        emoji = ""
        content = message

        if reply_type.value == "question":
            emoji = "↩️"  # ↩️
            content = f"{emoji} - {message}"
        elif reply_type.value == "answer":
            emoji = "💬"  # 💬
            content = f"{emoji} - {message}"
        elif reply_type.value == "review":
            if not rating:
                await interaction.response.send_message("Please provide a rating (1-5 stars) when adding a review.", ephemeral=True)
                return
            stars = "⭐" * rating
            content = f"{stars} - {message}"

        await thread.send(content)

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            await log_channel.send(
                f"[Reply - {reply_type.name}]\nAuthor: {interaction.user}\nThread: {thread.name}\nContent: {message}"
            )

        await interaction.response.send_message("Your anonymous reply has been posted.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
