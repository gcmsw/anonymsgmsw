import discord
from discord.ext import commands
from discord import app_commands
import os

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID"))
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508

class SubmitModal(discord.ui.Modal, title="Submit Anonymous Review"):
    def __init__(self, command_name: str):
        super().__init__()
        self.command_name = command_name
        self.site_name = discord.ui.TextInput(label="Site Name", required=True, max_length=100)
        self.message = discord.ui.TextInput(label="Your Message", required=True, max_length=1900, style=discord.TextStyle.paragraph)
        self.rating = discord.ui.TextInput(label="Rating (1-5 stars)", required=False, max_length=1)
        self.message_id = discord.ui.TextInput(label="Message ID (for replies only)", required=False)

        self.add_item(self.site_name)
        self.add_item(self.message)
        if self.command_name in ["anon-newsite", "anon-addreview"]:
            self.add_item(self.rating)
        if self.command_name == "anon-reply":
            self.add_item(self.message_id)

    async def on_submit(self, interaction: discord.Interaction):
        command = interaction.client.get_command(self.command_name)
        if command is None:
            await interaction.response.send_message("Command not found.", ephemeral=True)
            return

        # Assemble arguments
        if self.command_name == "anon-newsite":
            await interaction.client.tree.get_command("anon-newsite")._callback(
                command._callback.__self__,
                interaction,
                site_name=self.site_name.value,
                message=self.message.value,
                rating=int(self.rating.value),
            )
        elif self.command_name == "anon-addreview":
            await interaction.client.tree.get_command("anon-addreview")._callback(
                command._callback.__self__,
                interaction,
                thread_id=self.site_name.value,  # using site_name field for thread_id in modal
                message=self.message.value,
                rating=int(self.rating.value),
            )
        elif self.command_name == "anon-question":
            await interaction.client.tree.get_command("anon-question")._callback(
                command._callback.__self__,
                interaction,
                thread_id=self.site_name.value,
                message=self.message.value,
            )
        elif self.command_name == "anon-reply":
            await interaction.client.tree.get_command("anon-reply")._callback(
                command._callback.__self__,
                interaction,
                thread_id=self.site_name.value,
                message_id=self.message_id.value,
                message=self.message.value,
            )

class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="anon-newsite")
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-newsite"))

    @discord.ui.button(label="Add to Site Thread", style=discord.ButtonStyle.success, custom_id="anon-addreview")
    async def addreview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-addreview"))

    @discord.ui.button(label="Ask a Question", style=discord.ButtonStyle.secondary, custom_id="anon-question")
    async def question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-question"))

    @discord.ui.button(label="Reply to Message", style=discord.ButtonStyle.danger, custom_id="anon-reply")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-reply"))

class PostButtonsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Manually post the review buttons.")
    @app_commands.checks.has_role("Admin")
    async def post_buttons(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Could not find the submit-site-review channel.", ephemeral=True)
            return
        await channel.send("Use the buttons below to submit anonymously:", view=ReviewButtons())
        await interaction.response.send_message("Buttons posted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(PostButtonsCog(bot))
