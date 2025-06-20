from discord.ext import commands
from discord import app_commands, ui, Interaction, ButtonStyle
import discord
import os

# IDs
SUBMIT_CHANNEL_ID = 1381803347564171286
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508

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

class ReplyModal(ui.Modal, title="Reply to a Message"):
    thread_id = ui.TextInput(label="Thread ID", max_length=25)
    message_id = ui.TextInput(label="Message ID", max_length=25)
    message = ui.TextInput(label="Your Reply", style=discord.TextStyle.paragraph, max_length=1900)

    async def on_submit(self, interaction: Interaction):
        command_cog = interaction.client.get_cog("CommandsCog")
        await command_cog.anon_reply(interaction, self.thread_id.value, self.message_id.value, self.message.value)

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = LOG_CHANNEL_ID
        self.forum_channel_id = FORUM_CHANNEL_ID

    @app_commands.command(name="post-buttons", description="Post the button panel to the submit site review channel")
    async def post_buttons(self, interaction: Interaction):
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if channel:
            await channel.send("Click a button below to submit anonymously:", view=ReviewButtons())
            await interaction.response.send_message("✅ Buttons posted!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Could not find the submit-site-review channel.", ephemeral=True)

    @app_commands.command(name="anon-newsite", description="Submit a new anonymous review for a site")
    async def newsite(self, interaction: Interaction, site_name: str, message: str, rating: app_commands.Range[int, 1, 5]):
        forum_channel = self.bot.get_channel(self.forum_channel_id)
        log_channel = self.bot.get_channel(self.log_channel_id)

        for thread in forum_channel.threads:
            if thread.name.lower().strip() == site_name.lower().strip():
                sent_msg = await thread.send(f"{'⭐' * rating} - {message}")
                await interaction.response.send_message(f"✅ Review posted to existing thread: {thread.mention}", ephemeral=True)
                await log_channel.send(
                    f"[ANON REDIRECTED REVIEW]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nLink: {sent_msg.jump_url}"
                )
                return

        thread = await forum_channel.create_thread(name=site_name, content=f"{'⭐' * rating} - {message}")
        await interaction.response.send_message("✅ New review thread created.", ephemeral=True)
        await log_channel.send(
            f"[ANON NEW THREAD]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}"
        )

    @app_commands.command(name="anon-addreview", description="Add a review to an existing site thread")
    async def addreview(self, interaction: Interaction, thread_id: str, message: str, rating: app_commands.Range[int, 1, 5]):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if thread and isinstance(thread, discord.Thread):
            sent_msg = await thread.send(f"{'⭐' * rating} - {message}")
            await interaction.response.send_message("✅ Review posted to thread.", ephemeral=True)
            await log_channel.send(
                f"[ANON ADD REVIEW]\nThread: {thread.name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nLink: {sent_msg.jump_url}"
            )
        else:
            await interaction.response.send_message("⚠️ Could not find that thread.", ephemeral=True)

    @app_commands.command(name="anon-question", description="Ask a question anonymously in a thread")
    async def anon_question(self, interaction: Interaction, thread_id: str, message: str):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if thread and isinstance(thread, discord.Thread):
            sent_msg = await thread.send(f"❓ {message}")
            await interaction.response.send_message("✅ Question posted.", ephemeral=True)
            await log_channel.send(
                f"[ANON QUESTION]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nLink: {sent_msg.jump_url}"
            )
        else:
            await interaction.response.send_message("⚠️ Could not find that thread.", ephemeral=True)

    @app_commands.command(name="anon-reply", description="Reply anonymously to a message in a thread")
    async def anon_reply(self, interaction: Interaction, thread_id: str, message_id: str, message: str):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(self.log_channel_id)

        if thread and isinstance(thread, discord.Thread):
            try:
                ref_msg = await thread.fetch_message(int(message_id))
                sent_msg = await thread.send(f"↩️ {message}", reference=ref_msg)
                await interaction.response.send_message("✅ Reply posted.", ephemeral=True)
                await log_channel.send(
                    f"[ANON REPLY]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nLink: {sent_msg.jump_url}"
                )
            except discord.NotFound:
                await interaction.response.send_message("⚠️ Could not find the message to reply to.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Could not find that thread.", ephemeral=True)

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
            if not isinstance(thread, discord.Thread):
                return []
            messages = [
                message async for message in thread.history(limit=50)
                if current in str(message.id) or current.lower() in message.content.lower()
            ]
            return [
                app_commands.Choice(name=(msg.content[:50] + "...") if len(msg.content) > 50 else msg.content, value=str(msg.id))
                for msg in messages
            ][:25]
        except:
            return []

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
