import os
import discord
from discord.ext import commands
from discord import app_commands

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.log_channel_id = int(os.environ["LOG_CHANNEL_ID"])  # Logs go here
            self.commands_channel_id = int(os.environ["COMMANDS_CHANNEL_ID"])  # Anonymous messages go here
        except KeyError as e:
            raise RuntimeError(f"Missing required environment variable: {e}")

    @app_commands.command(
        name="sendanonymously",
        description="Send an anonymous message in the #Commands channel (Only staff will see your name)"
    )
    @app_commands.describe(message="The message you want to send (up to 1900 characters)")
    async def sendmsg(self, interaction: discord.Interaction, message: str):
        if len(message) > 1900:
            await interaction.response.send_message("Your message exceeds the 1900 character limit.", ephemeral=True)
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        commands_channel = self.bot.get_channel(self.commands_channel_id)

        # ✅ Join the thread if it's a forum post (thread)
        if isinstance(commands_channel, discord.Thread):
            await commands_channel.join()

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
            await interaction.response.send_message(
                content="One or more of the required channels was not found. Please reach out to Staff or Developers.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
