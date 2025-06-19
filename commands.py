import discord
from discord import app_commands
from discord.ext import commands
import os

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID"))
GUILD_ID = int(os.getenv("GUILD_ID"))

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_thread_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete threads from the specified forum channel."""
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if not isinstance(channel, discord.ForumChannel):
            return []

        threads = channel.threads
        return [
            app_commands.Choice(name=thread.name, value=str(thread.id))
            for thread in threads
            if current.lower() in thread.name.lower()
        ][:25]

    async def get_message_autocomplete(self, interaction: discord.Interaction, current: str):
        """Placeholder autocomplete for messages – returns empty list (not implemented)."""
        return []

    @app_commands.command(name="anon-review", description="Submit an anonymous site review")
    async def anon_review(self, interaction: discord.Interaction, site: str, review: str):
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if not isinstance(channel, discord.ForumChannel):
            await interaction.response.send_message("Forum channel not found.", ephemeral=True)
            return

        thread = await channel.create_thread(name=site, content=f"**Anonymous Site Review**\n{review}")
        await interaction.response.send_message("✅ Your anonymous review has been posted!", ephemeral=True)

    @app_commands.command(name="anon-addreview", description="Add an anonymous review to an existing thread")
    @app_commands.autocomplete(thread_id=get_thread_autocomplete)
    async def anon_addreview(self, interaction: discord.Interaction, thread_id: str, review: str):
        thread = await self.bot.fetch_channel(int(thread_id))
        if not isinstance(thread, discord.Thread):
            await interaction.response.send_message("Thread not found.", ephemeral=True)
            return

        await thread.send(f"**Follow-up Anonymous Review**\n{review}")
        await interaction.response.send_message("✅ Your follow-up review has been posted!", ephemeral=True)

    @app_commands.command(name="anon-question", description="Ask an anonymous question")
    async def anon_question(self, interaction: discord.Interaction, topic: str, question: str):
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if not isinstance(channel, discord.ForumChannel):
            await interaction.response.send_message("Forum channel not found.", ephemeral=True)
            return

        thread = await channel.create_thread(name=topic, content=f"**Anonymous Question**\n{question}")
        await interaction.response.send_message("✅ Your anonymous question has been posted!", ephemeral=True)

    @app_commands.command(name="anon-reply", description="Reply anonymously to a message in a thread")
    @app_commands.autocomplete(thread_id=get_thread_autocomplete, message_id=get_message_autocomplete)
    async def anon_reply(self, interaction: discord.Interaction, thread_id: str, message_id: str, reply: str):
        thread = await self.bot.fetch_channel(int(thread_id))
        if not isinstance(thread, discord.Thread):
            await interaction.response.send_message("Thread not found.", ephemeral=True)
            return

        await thread.send(f"**Anonymous Reply**\n{reply}")
        await interaction.response.send_message("✅ Your anonymous reply has been posted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
