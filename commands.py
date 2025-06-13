from discord.ext import commands
from discord import app_commands
import discord
import os

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(os.getenv("LOG_CHANNEL_ID"))
        self.commands_channel_id = int(os.getenv("COMMANDS_CHANNEL_ID"))

    @app_commands.command(
        name="sendanonymously",
        description="Send an anonymous message in the #Commands channel (only staff will see your name)"
    )
    @app_commands.describe(message="The message you want to send (up to 1900 characters)")
    async def sendmsg(self, interaction: discord.Interaction, message: str):
        if len(message) > 1900:
            await interaction.response.send_message("Your message exceeds the 1900 character limit.", ephemeral=True)
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        commands_channel = self.bot.get_channel(self.commands_channel_id)

        log_msg = f"Author: {interaction.user}\nAuthor ID: {interaction.user.id}\nContent: {message}"
        anon_msg = f"Author: Anonymous\nContent: {message}"

        if log_channel:
            await log_channel.send(log_msg)
        if commands_channel:
            await commands_channel.send(anon_msg)

        if log_channel or commands_channel:
            await interaction.response.send_message("✅ Your message has been sent.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "⚠️ One or more of the required channels was not found.",
                ephemeral=True
            )

    async def cog_load(self):
        self.bot.tree.add_command(self.sendmsg)

async def setup(bot: commands.Bot):
    await bot.add_cog(CommandsCog(bot))
