import discord
from discord import app_commands
from discord.ext import commands
import os

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID", "0"))
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508

class SubmitModal(discord.ui.Modal):
    def __init__(self, command_name: str):
        super().__init__(title="Submit Anonymously")
        self.command_name = command_name

        self.site_name = discord.ui.TextInput(label="Site Name", required=False)
        self.message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph)
        self.rating = discord.ui.TextInput(label="Rating (1-5 stars)", required=False)

        self.add_item(self.site_name)
        self.add_item(self.message)
        self.add_item(self.rating)

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("CommandsCog")
        if self.command_name == "anon-newsite":
            await cog.newsite(interaction, self.site_name.value, self.message.value, int(self.rating.value))
        elif self.command_name == "anon-addreview":
            await cog.addreview(interaction, self.site_name.value, self.message.value, int(self.rating.value))
        elif self.command_name == "anon-question":
            await cog.anon_question(interaction, self.site_name.value, self.message.value)
        elif self.command_name == "anon-reply":
            await cog.anon_reply(interaction, self.site_name.value, self.message.value, self.rating.value)
        else:
            await interaction.response.send_message("Unknown form submission.", ephemeral=True)

class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary)
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-newsite"))

    @discord.ui.button(label="Add Review", style=discord.ButtonStyle.primary)
    async def addreview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-addreview"))

    @discord.ui.button(label="Ask a Question", style=discord.ButtonStyle.primary)
    async def question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-question"))

    @discord.ui.button(label="Reply to Message", style=discord.ButtonStyle.primary)
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-reply"))

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Post the anonymous submit buttons")
    async def post_buttons(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return

        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Could not find the submit channel.", ephemeral=True)
            return

        await channel.send("Use the buttons below to submit anonymously:", view=ReviewButtons())
        await interaction.response.send_message("Buttons posted!", ephemeral=True)

    # Your original commands go here: newsite, addreview, anon_question, anon_reply, autocomplete
    # Make sure they don't use interaction.response.send_message more than once if being reused by modal

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
