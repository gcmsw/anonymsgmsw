from discord.ext import commands
from discord import app_commands, ui, Interaction, ButtonStyle
import discord
import os

# ========== UI MODALS ==========

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

# ========== MODALS ==========

class NewSiteReviewModal(ui.Modal, title="Submit New Site Review"):
    site_name = ui.TextInput(label="Site Name", max_length=100)
    message = ui.TextInput(label="Your Review", style=discord.TextStyle.paragraph, max_length=1900)
    rating = ui.TextInput(label="Star Rating (1-5)", max_length=1)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.newsite(interaction, self.site_name.value, self.message.value, int(self.rating.value))

class AddReviewModal(ui.Modal, title="Add Review to Existing Site"):
    thread_id = ui.TextInput(label="Thread ID", max_length=25)
    message = ui.TextInput(label="Your Review", style=discord.TextStyle.paragraph, max_length=1900)
    rating = ui.TextInput(label="Star Rating (1-5)", max_length=1)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.addreview(interaction, self.thread_id.value, self.message.value, int(self.rating.value))

class QuestionModal(ui.Modal, title="Ask a Question"):
    thread_id = ui.TextInput(label="Thread ID", max_length=25)
    message = ui.TextInput(label="Your Question", style=discord.TextStyle.paragraph, max_length=1900)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.anon_question(interaction, self.thread_id.value, self.message.value)

class ReplyModal(ui.Modal, title="Reply in a Thread"):
    thread_id = ui.TextInput(label="Thread ID", max_length=25)
    message_id = ui.TextInput(label="Message ID")
    message = ui.TextInput(label="Your Reply", style=discord.TextStyle.paragraph, max_length=1900)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.anon_reply(interaction, self.thread_id.value, self.message_id.value, self.message.value)

# ========== COMMANDS ==========

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = int(os.environ.get("LOG_CHANNEL_ID"))
        self.forum_channel_id = int(os.environ.get("FORUM_CHANNEL_ID"))

    # Utilities
    async def send_anonymous_message(self, thread_id, message, embed=None):
        channel = self.bot.get_channel(self.forum_channel_id)
        thread = channel.get_thread(int(thread_id))
        if thread:
            await thread.send(content=message, embed=embed)

    # Slash command: newsite
    @app_commands.command(name="anon-newsite", description="Start a new anonymous site review")
    async def newsite(self, interaction: Interaction, site_name: str, message: str, rating: int):
        channel = self.bot.get_channel(self.forum_channel_id)
        thread = await channel.create_thread(name=f"{site_name} ⭐ {rating}", content=message)
        await interaction.response.send_message("✅ Your review has been posted anonymously.", ephemeral=True)

    # Slash command: addreview
    @app_commands.command(name="anon-addreview", description="Add an anonymous review to an existing thread")
    @app_commands.autocomplete(thread_id="get_thread_autocomplete")
    async def addreview(self, interaction: Interaction, thread_id: str, message: str, rating: int):
        await self.send_anonymous_message(thread_id, f"⭐ {rating}\n{message}")
        await interaction.response.send_message("✅ Your review has been added anonymously.", ephemeral=True)

    # Slash command: anon-question
    @app_commands.command(name="anon-question", description="Ask an anonymous question in an existing thread")
    @app_commands.autocomplete(thread_id="get_thread_autocomplete")
    async def anon_question(self, interaction: Interaction, thread_id: str, message: str):
        await self.send_anonymous_message(thread_id, f"❓ {message}")
        await interaction.response.send_message("✅ Your question has been sent anonymously.", ephemeral=True)

    # Slash command: anon-reply
    @app_commands.command(name="anon-reply", description="Reply to a specific message in a thread anonymously")
    @app_commands.autocomplete(thread_id="get_thread_autocomplete")
    async def anon_reply(self, interaction: Interaction, thread_id: str, message_id: str, message: str):
        channel = self.bot.get_channel(self.forum_channel_id)
        thread = channel.get_thread(int(thread_id))
        if thread:
            try:
                msg_to_reply = await thread.fetch_message(int(message_id))
                await msg_to_reply.reply(message)
                await interaction.response.send_message("✅ Your reply has been posted anonymously.", ephemeral=True)
            except:
                await interaction.response.send_message("⚠️ Couldn't find that message.", ephemeral=True)

    # Autocomplete helper
    async def get_thread_autocomplete(self, interaction: Interaction, current: str):
        channel = self.bot.get_channel(self.forum_channel_id)
        threads = await channel.active_threads()
        return [
            app_commands.Choice(name=t.name, value=str(t.id))
            for t in threads if current.lower() in t.name.lower()
        ][:25]

# ========== BUTTON PANEL ==========

class ButtonPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        channel_id = int(os.environ.get("SUBMIT_CHANNEL_ID"))
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send("Click a button below to submit anonymously:", view=ReviewButtons())

# ========== SETUP ==========

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
    await bot.add_cog(ButtonPanel(bot))
