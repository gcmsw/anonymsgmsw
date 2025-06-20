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

    @app_commands.command(name="anon-newsite", description="Submit a new anonymous review for a site")
    @app_commands.describe(site_name="Name of the site", message="Your review", rating="Star rating 1-5")
    async def newsite(self, interaction: Interaction, site_name: str, message: str, rating: app_commands.Range[int, 1, 5]):
        forum_channel = self.bot.get_channel(self.forum_channel_id)
        log_channel = self.bot.get_channel(self.log_channel_id)
        stars = "⭐" * rating
        post_content = f"{stars} - {message}"

        for thread in forum_channel.threads:
            if thread.name.strip().lower() == site_name.strip().lower():
                sent_msg = await thread.send(post_content)
                await log_channel.send(f"[ANON REDIRECTED REVIEW]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nThread: {sent_msg.jump_url}")
                await interaction.response.send_message(f"Site already exists. Posted in {thread.mention}.", ephemeral=True)
                return

        thread = await forum_channel.create_thread(name=site_name, content=post_content)
        sent_msg = await thread.fetch_message(thread.id)
        await log_channel.send(f"[ANON NEW THREAD]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}")
        await interaction.response.send_message("Your anonymous review has been submitted.", ephemeral=True)

    @app_commands.command(name="anon-addreview", description="Add a review to an existing site thread")
    @app_commands.describe(thread_id="Thread to post in", message="Your review", rating="Star rating 1-5")
    async def addreview(self, interaction: Interaction, thread_id: str, message: str, rating: app_commands.Range[int, 1, 5]):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)
        if thread and isinstance(thread, discord.Thread):
            stars = "⭐" * rating
            sent_msg = await thread.send(f"{stars} - {message}")
            await log_channel.send(f"[ANON ADD REVIEW]\nThread: {thread.name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
            await interaction.response.send_message("Your anonymous review was posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @app_commands.command(name="anon-question", description="Ask a question anonymously in a thread")
    @app_commands.describe(thread_id="Thread to ask in", message="Your question")
    async def anon_question(self, interaction: Interaction, thread_id: str, message: str):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)
        if thread and isinstance(thread, discord.Thread):
            sent_msg = await thread.send(f"❓ - {message}")
            await log_channel.send(f"[ANON QUESTION]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
            await interaction.response.send_message("Your anonymous question was posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @app_commands.command(name="anon-reply", description="Reply anonymously in a thread to a message")
    @app_commands.describe(thread_id="Thread to reply in", message_id="ID of the message to reply to", message="Your reply")
    async def anon_reply(self, interaction: Interaction, thread_id: str, message_id: str, message: str):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)
        if thread and isinstance(thread, discord.Thread):
            try:
                reference_msg = await thread.fetch_message(int(message_id))
                sent_msg = await thread.send(f"↩️ - {message}", reference=reference_msg)
                await log_channel.send(f"[ANON REPLY]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
                await interaction.response.send_message("Your anonymous reply was posted.", ephemeral=True)
            except discord.NotFound:
                await interaction.response.send_message("Could not find that message in the thread.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @addreview.autocomplete("thread_id")
    @anon_question.autocomplete("thread_id")
    @anon_reply.autocomplete("thread_id")
    async def thread_id_autocomplete(self, interaction: Interaction, current: str):
        forum_channel = self.bot.get_channel(self.forum_channel_id)
        if not isinstance(forum_channel, discord.ForumChannel):
            return []
        return [
            app_commands.Choice(name=thread.name, value=str(thread.id))
            for thread in forum_channel.threads
            if current.lower() in thread.name.lower()
        ][:25]

    @anon_reply.autocomplete("message_id")
    async def message_id_autocomplete(self, interaction: Interaction, current: str):
        thread_id = interaction.namespace.thread_id
        try:
            thread = self.bot.get_channel(int(thread_id))
            messages = [
                message async for message in thread.history(limit=50)
                if current in str(message.id) or current.lower() in message.content.lower()
            ]
            return [
                app_commands.Choice(name=f"{m.content[:50]}..." if len(m.content) > 50 else m.content, value=str(m.id))
                for m in messages
            ][:25]
        except:
            return []

class ButtonPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        channel_id = 1381803347564171286  # #submit-site-review
        channel = self.bot.get_channel(channel_id)
        if channel:
            try:
                await channel.send("Click a button below to submit anonymously:", view=ReviewButtons())
                print("✅ Button panel sent successfully.")
            except Exception as e:
                print(f"❌ Failed to send button panel: {e}")

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
    await bot.add_cog(ButtonPanel(bot))
