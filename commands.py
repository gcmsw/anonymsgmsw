import os
import discord
from discord.ext import commands
from discord import app_commands

# Pull env vars from Render
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
COMMANDS_CHANNEL_ID = int(os.getenv("COMMANDS_CHANNEL_ID"))

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = LOG_CHANNEL_ID
        self.commands_channel_id = COMMANDS_CHANNEL_ID

    @app_commands.command(
        name="sendanonymously",
        description="Send an anonymous message in the Commands channel (Only staff will see your name)"
    )
    @app_commands.describe(message="The message you want to send (up to 1900 characters)")
    async def sendmsg(self, interaction: discord.Interaction, message: str):
        if len(message) > 1900:
            await interaction.response.send_message("Your message exceeds the 1900 character limit.", ephemeral=True)
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        commands_channel = self.bot.get_channel(self.commands_channel_id)

        log_message_content = (
            f"Author: {interaction.user}\n"
            f"Author ID: {interaction.user.id}\n"
            f"Content: {message}"
        )
        commands_message_content = (
            f"Author: Anonymous\n"
            f"Content: {message}"
        )

        if log_channel:
            await log_channel.send(log_message_content)
        if commands_channel:
            await commands_channel.send(commands_message_content)

        if log_channel or commands_channel:
            await interaction.response.send_message(content="Your message has been sent.", ephemeral=True)
        else:
            await interaction.response.send_message(content="Channels not found. Please contact staff.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
