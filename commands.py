import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

SUBMIT_CHANNEL_ID = 123456789012345678  # Replace with your submit channel ID

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_thread_autocomplete(self, interaction: discord.Interaction, current: str):
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        threads = await channel.threads()  # FORUM CHANNEL!
        return [
            app_commands.Choice(name=thread.name, value=str(thread.id))
            for thread in threads if current.lower() in thread.name.lower()
        ]

    async def get_message_autocomplete(self, interaction: discord.Interaction, current: str):
        thread = interaction.namespace.thread_id
        try:
            thread_channel = await self.bot.fetch_channel(int(thread))
            messages = [message async for message in thread_channel.history(limit=50)]
            return [
                Choice(name=f"{m.author.name}: {m.content[:50]}", value=str(m.id))
                for m in messages if current.lower() in m.content.lower()
            ]
        except:
            return []

    @app_commands.command(name="anon-reply", description="Reply anonymously to a message in a thread")
    @app_commands.describe(thread_id="Select the thread", message_id="Select a message to reply to", reply_content="Your anonymous reply")
    @app_commands.autocomplete(thread_id=get_thread_autocomplete, message_id=get_message_autocomplete)
    async def anon_reply(self, interaction: discord.Interaction, thread_id: str, message_id: str, reply_content: str):
        thread = await self.bot.fetch_channel(int(thread_id))
        try:
            message = await thread.fetch_message(int(message_id))
            await message.reply(reply_content)
            await interaction.response.send_message("✅ Anonymous reply sent.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
