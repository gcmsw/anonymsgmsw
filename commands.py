import discord
from discord import app_commands
from discord.ext import commands
import os

# Constants
SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID"))
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID"))

# ReviewButtons View
class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="new_review")
    async def new_review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NewReviewModal())

    @discord.ui.button(label="Add to Existing Review", style=discord.ButtonStyle.secondary, custom_id="add_review")
    async def add_review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddReviewModal())

    @discord.ui.button(label="Ask a Question", style=discord.ButtonStyle.success, custom_id="ask_question")
    async def ask_question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AskQuestionModal())

    @discord.ui.button(label="Reply to a Thread", style=discord.ButtonStyle.success, custom_id="reply")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReplyModal())

# Modal Classes
class NewReviewModal(discord.ui.Modal, title="New Site Review"):
    site_name = discord.ui.TextInput(label="Site Name", required=True)
    review = discord.ui.TextInput(label="Review", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        forum = interaction.client.get_channel(FORUM_CHANNEL_ID)
        thread = await forum.create_thread(name=self.site_name.value)
        await thread.send(f"📍 **Anonymous Site Review:**\n{self.review.value}")
        await interaction.response.send_message("✅ Review posted anonymously!", ephemeral=True)

class AddReviewModal(discord.ui.Modal, title="Add Review to Existing Thread"):
    thread_id = discord.ui.TextInput(label="Thread ID", placeholder="Paste thread ID here", required=True)
    review = discord.ui.TextInput(label="Review", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        thread = interaction.client.get_channel(int(self.thread_id.value))
        if isinstance(thread, discord.Thread):
            await thread.send(f"📝 **Additional Anonymous Review:**\n{self.review.value}")
            await interaction.response.send_message("✅ Added review anonymously!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Invalid thread ID.", ephemeral=True)

class AskQuestionModal(discord.ui.Modal, title="Ask an Anonymous Question"):
    question = discord.ui.TextInput(label="Your Question", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        submit_channel = interaction.client.get_channel(SUBMIT_CHANNEL_ID)
        await submit_channel.send(f"❓ **Anonymous Question:**\n{self.question.value}")
        await interaction.response.send_message("✅ Question sent anonymously!", ephemeral=True)

class ReplyModal(discord.ui.Modal, title="Reply to a Thread"):
    thread_id = discord.ui.TextInput(label="Thread ID", placeholder="Paste thread ID here", required=True)
    reply = discord.ui.TextInput(label="Reply", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        thread = interaction.client.get_channel(int(self.thread_id.value))
        if isinstance(thread, discord.Thread):
            await thread.send(f"💬 **Anonymous Reply:**\n{self.reply.value}")
            await interaction.response.send_message("✅ Reply sent anonymously!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Invalid thread ID.", ephemeral=True)

# Autocomplete helper
async def thread_autocomplete(interaction: discord.Interaction, current: str):
    forum = interaction.client.get_channel(FORUM_CHANNEL_ID)
    threads = forum.threads
    return [
        app_commands.Choice(name=thread.name, value=str(thread.id))
        for thread in threads if current.lower() in thread.name.lower()
    ][:25]

# Cog
class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="respondanon", description="Reply anonymously to a thread")
    @app_commands.describe(thread_id="Pick a thread to reply to")
    @app_commands.autocomplete(thread_id=thread_autocomplete)
    async def anon_reply(self, interaction: discord.Interaction, thread_id: str, message: str):
        thread = interaction.client.get_channel(int(thread_id))
        if isinstance(thread, discord.Thread):
            await thread.send(f"💬 **Anonymous Reply:**\n{message}")
            await interaction.response.send_message("✅ Reply sent anonymously!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Invalid thread ID.", ephemeral=True)

    @app_commands.command(name="anon-addreview", description="Add an anonymous review to an existing thread")
    @app_commands.describe(thread_id="Pick a thread to add a review to")
    @app_commands.autocomplete(thread_id=thread_autocomplete)
    async def anon_addreview(self, interaction: discord.Interaction, thread_id: str, review: str):
        thread = interaction.client.get_channel(int(thread_id))
        if isinstance(thread, discord.Thread):
            await thread.send(f"📝 **Additional Anonymous Review:**\n{review}")
            await interaction.response.send_message("✅ Review added anonymously!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Invalid thread ID.", ephemeral=True)

# Second Cog for button view registration
class ButtonPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="show-buttons", description="Post the interactive anonymous submission panel")
    async def show_buttons(self, interaction: discord.Interaction):
        view = ReviewButtons()
        await interaction.response.send_message(
            "🗂️ Use the buttons below to post anonymously to the forum.",
            view=view
        )

# Setup
async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
    await bot.add_cog(ButtonPanel(bot))
