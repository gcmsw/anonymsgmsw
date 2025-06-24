import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
import os
import logging
from utils import is_staff, post_help_buttons, find_forum_channel, fetch_message_autocomplete

FIELD_REVIEW_SUBMIT_CHANNEL_ID = int(os.getenv("FIELD_REVIEW_SUBMIT_CHANNEL_ID"))
FIELD_FORUM_CHANNEL_ID = int(os.getenv("FIELD_FORUM_CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

logger = logging.getLogger(__name__)

class SubmitModal(Modal, title="Submit a New Site Review"):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

        self.site_name = TextInput(label="Site Name", placeholder="e.g., EMQ Cupertino", max_length=100)
        self.review = TextInput(label="Your Review", style=discord.TextStyle.paragraph, max_length=1000)
        self.field_type = TextInput(label="Field Type (optional)", required=False, placeholder="e.g., School Social Work")

        self.add_item(self.site_name)
        self.add_item(self.review)
        self.add_item(self.field_type)

    async def on_submit(self, interaction: discord.Interaction):
        forum = find_forum_channel(interaction.guild, FIELD_FORUM_CHANNEL_ID)
        if not forum:
            await interaction.response.send_message("Forum channel not found.", ephemeral=True)
            return

        thread = discord.utils.get(forum.threads, name=self.site_name.value)
        if thread:
            await interaction.response.send_message(f"A thread for **{self.site_name.value}** already exists. Please add your review there.", ephemeral=True)
            return

        content = f"**Anonymous Review:**\n{self.review.value}"
        if self.field_type.value:
            content = f"**Field Type:** {self.field_type.value}\n\n{content}"

        thread = await forum.create_thread(name=self.site_name.value, content=content)
        await post_help_buttons(thread, self.bot)

        await interaction.response.send_message(f"Thread for **{self.site_name.value}** created successfully!", ephemeral=True)

class ReviewButtons(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Submit New Site Review", style=discord.ButtonStyle.primary)
    async def submit_site(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SubmitModal(self.bot))

class HelpButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="How to Post Anonymously", style=discord.ButtonStyle.secondary)
    async def how_to_post(self, interaction: discord.Interaction, button: Button):
        help_text = (
            "Use the following slash commands in this thread to post anonymously:\n"
            "• `/anon-addreview` — Add another review\n"
            "• `/anon-question` — Ask a question\n"
            "• `/anon-reply` — Reply to a message\n\n"
            "Use autocomplete to target specific messages if needed."
        )
        await interaction.response.send_message(help_text, ephemeral=True)

class CommandTree(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anon-newsite", description="Create a new thread to review a site anonymously")
    async def anon_newsite(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SubmitModal(self.bot))

    @app_commands.command(name="anon-addreview", description="Add a review to an existing thread")
    @app_commands.describe(review="Your anonymous review")
    async def anon_addreview(self, interaction: discord.Interaction, review: str):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Please use this command inside a site review thread.", ephemeral=True)
            return
        await interaction.channel.send(f"**Anonymous Review:**\n{review}")
        await interaction.response.send_message("Your anonymous review was posted.", ephemeral=True)

    @app_commands.command(name="anon-question", description="Ask a question anonymously in a thread")
    @app_commands.describe(question="Your anonymous question")
    async def anon_question(self, interaction: discord.Interaction, question: str):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Please use this command inside a site review thread.", ephemeral=True)
            return
        await interaction.channel.send(f"**Anonymous Question:**\n{question}")
        await interaction.response.send_message("Your anonymous question was posted.", ephemeral=True)

    @app_commands.command(name="anon-reply", description="Reply anonymously to a message in a thread")
    @app_commands.describe(message_id="The message ID to reply to", reply="Your anonymous reply")
    @app_commands.autocomplete(message_id=fetch_message_autocomplete)
    async def anon_reply(self, interaction: discord.Interaction, message_id: str, reply: str):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("Please use this command inside a site review thread.", ephemeral=True)
            return
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            await message.reply(f"**Anonymous Reply:**\n{reply}")
            await interaction.response.send_message("Your anonymous reply was posted.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("Could not find the target message.", ephemeral=True)

    @app_commands.command(name="post-buttons", description="(Admin) Post persistent review buttons")
    async def post_buttons(self, interaction: discord.Interaction):
        if not is_staff(interaction):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        channel = self.bot.get_channel(FIELD_REVIEW_SUBMIT_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Submit channel not found.", ephemeral=True)
            return
        async for msg in channel.history(limit=10):
            if msg.author == self.bot.user:
                await msg.delete()
        await channel.send("Click below to submit a new site review anonymously:", view=ReviewButtons(self.bot))
        await interaction.response.send_message("Button panel posted!", ephemeral=True)

def setup(bot):
    bot.add_cog(CommandTree(bot))
