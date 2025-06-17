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
        except KeyError as e:
            raise RuntimeError(f"Missing required environment variable: {e}")

    @app_commands.command(name="sendanonymously", description="Send an anonymous message (Only staff will see your name)")
    @app_commands.describe(message="The message you want to send (up to 1900 characters)")
    async def sendmsg(self, interaction: discord.Interaction, message: str):
        if len(message) > 1900:
            await interaction.response.send_message("Your message exceeds the 1900 character limit.", ephemeral=True)
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        commands_channel = self.bot.get_channel(self.commands_channel_id)

        # 🔍 Debug print to check what kind of channel it is
        print(f"commands_channel: {commands_channel} — type: {type(commands_channel)}")

        log_message_content = (
            f"Author: {interaction.user}\n"
            f"Author ID: {interaction.user.id}\n"
            f"Content: {message}"
        )

        commands_message_content = message  # Clean version — just the message

        if log_channel:
            await log_channel.send(log_message_content)
        if commands_channel:
            await commands_channel.send(commands_message_content)

        if log_channel or commands_channel:
            await interaction.response.send_message(content="Your message has been sent.", ephemeral=_
