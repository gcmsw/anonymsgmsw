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
        self.log_channel_id = 1382563380367331429
        self.forum_channel_id = 1384999875237646508

    @app_commands.command(name="anon-newsite", description="Post an anonymous review in a new thread.")
    async def newsite(self, interaction: Interaction, site_name: str, message: str, rating: int):
        forum = interaction.guild.get_channel(self.forum_channel_id)
        thread = await forum.create_thread(name=f"{site_name} ⭐{rating}", content=message)
        await interaction.response.send_message("✅ Your anonymous review has been posted.", ephemeral=True)
        log = interaction.guild.get_channel(self.log_channel_id)
        await log.send(f"🆕 Anonymous review posted for `{site_name}` with ⭐{rating}:\n{message}\nThread: {thread.jump_url}")

    @app_commands.command(name="anon-addreview", description="Add an anonymous review to an existing thread.")
    @app_commands.describe(thread_id="The ID of the thread", message="Your review", rating="1–5 stars")
    async def addreview(self, interaction: Interaction, thread_id: str, message: str, rating: int):
        thread = interaction.guild.get_thread(int(thread_id))
        await thread.send(f"⭐{rating} Anonymous Review:\n{message}")
        await interaction.response.send_message("✅ Your review was added anonymously.", ephemeral=True)
        log = interaction.guild.get_channel(self.log_channel_id)
        await log.send(f"⭐ Anonymous follow-up review added:\n{message}\nThread: {thread.jump_url}")

    @app_commands.command(name="anon-question", description="Ask an anonymous question in a thread.")
    async def anon_question(self, interaction: Interaction, thread_id: str, message: str):
        thread = interaction.guild.get_thread(int(thread_id))
        await thread.send(f"❓ Anonymous Question:\n{message}")
        await interaction.response.send_message("✅ Your question was posted anonymously.", ephemeral=True)
        log = interaction.guild.get_channel(self.log_channel_id)
        await log.send(f"❓ Anonymous question added:\n{message}\nThread: {thread.jump_url}")

    @app_commands.command(name="anon-reply", description="Post an anonymous reply to a specific message.")
    async def anon_reply(self, interaction: Interaction, thread_id: str, message_id: str, message: str):
        thread = interaction.guild.get_thread(int(thread_id))
        original = await thread.fetch_message(int(message_id))
        await original.reply(f"↩️ Anonymous Reply:\n{message}")
        await interaction.response.send_message("✅ Your reply was posted anonymously.", ephemeral=True)
        log = interaction.guild.get_channel(self.log_channel_id)
        await log.send(f"↩️ Anonymous reply:\n{message}\nThread: {thread.jump_url}")

class ButtonPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        channel_id = int(os.environ.get("SUBMIT_CHANNEL_ID"))
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send("Click a button below to get started anonymously:", view=ReviewButtons())
            print("✅ Button view sent to SUBMIT_CHANNEL_ID")
        else:
            print("❌ SUBMIT_CHANNEL_ID not found or bot can't access it")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
    await bot.add_cog(ButtonPanel(bot))
    print("✅ All cogs loaded")
