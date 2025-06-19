from discord.ext import commands
from discord import app_commands, ui, Interaction, ButtonStyle
import discord
import os

class ReviewButtons(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🆕 New Site Review", style=ButtonStyle.primary, custom_id="newsite")
    async def new_site_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(NewSiteReviewModal())

    @ui.button(label="⭐ Add Review", style=ButtonStyle.secondary, custom_id="addreview")
    async def add_review_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(AddReviewModal())

    @ui.button(label="❓ Ask Question", style=ButtonStyle.success, custom_id="question")
    async def ask_question_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(QuestionModal())

    @ui.button(label="↩️ Reply", style=ButtonStyle.danger, custom_id="reply")
    async def reply_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(ReplyModal())

class NewSiteReviewModal(ui.Modal, title="Submit New Site Review"):
    site_name = ui.TextInput(label="Site Name", max_length=100)
    message = ui.TextInput(label="Your Review", style=discord.TextStyle.paragraph, max_length=1900)
    rating = ui.TextInput(label="Star Rating (1-5)", max_length=1)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.newsite(interaction, self.site_name.value, self.message.value, int(self.rating.value))

class AddReviewModal(ui.Modal, title="Add Review to Existing Site"):
    thread_id = ui.TextInput(label="Thread ID", placeholder="Paste the thread ID here", max_length=25)
    message = ui.TextInput(label="Your Review", style=discord.TextStyle.paragraph, max_length=1900)
    rating = ui.TextInput(label="Star Rating (1-5)", max_length=1)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.addreview(interaction, self.thread_id.value, self.message.value, int(self.rating.value))

class QuestionModal(ui.Modal, title="Ask a Question"):
    thread_id = ui.TextInput(label="Thread ID", placeholder="Paste the thread ID here", max_length=25)
    message = ui.TextInput(label="Your Question", style=discord.TextStyle.paragraph, max_length=1900)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.anon_question(interaction, self.thread_id.value, self.message.value)

class ReplyModal(ui.Modal, title="Reply in a Thread"):
    thread_id = ui.TextInput(label="Thread ID", placeholder="Paste the thread ID here", max_length=25)
    message_id = ui.TextInput(label="Message ID", placeholder="Paste the message ID you want to reply to")
    message = ui.TextInput(label="Your Reply", style=discord.TextStyle.paragraph, max_length=1900)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.anon_reply(interaction, self.thread_id.value, self.message_id.value, self.message.value)

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1382563380367331429  # Log channel
        self.forum_channel_id = 1384999875237646508  # Forum channel

    # Slash commands go here (same as in your original code... omitted for brevity)
    # Include all of anon-newsite, anon-addreview, anon-question, anon-reply and their autocompletes
    # (Can paste back if needed)

class ButtonPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        channel_id = int(os.environ.get("SUBMIT_CHANNEL_ID"))
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send("Click a button below to get started anonymously:", view=ReviewButtons())

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
    await bot.add_cog(ButtonPanel(bot))
