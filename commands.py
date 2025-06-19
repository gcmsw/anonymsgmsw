from discord.ext import commands
from discord import app_commands
import discord
import os

SUBMIT_CHANNEL_ID = 1381803347564171286
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anon-newsite", description="Submit a new anonymous review for a site")
    @app_commands.describe(site_name="Name of the site", message="Your review (up to 1900 characters)", rating="Star rating 1-5")
    async def newsite(self, interaction: discord.Interaction, site_name: str, message: str, rating: app_commands.Range[int, 1, 5]):
        forum_channel = self.bot.get_channel(FORUM_CHANNEL_ID)
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        stars = "⭐" * rating
        post_content = f"{stars} - {message}"

        for thread in forum_channel.threads:
            if thread.name.strip().lower() == site_name.strip().lower():
                sent_msg = await thread.send(post_content)
                await log_channel.send(
                    f"[ANON REDIRECTED REVIEW]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nThread: {sent_msg.jump_url}"
                )
                await interaction.response.send_message(f"Review posted to existing thread: {thread.mention}", ephemeral=True)
                return

        thread = await forum_channel.create_thread(name=site_name, content=post_content)
        await log_channel.send(
            f"[ANON NEW THREAD]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nThread: {thread.jump_url}"
        )
        await interaction.response.send_message("Your anonymous review has been submitted.", ephemeral=True)

    @app_commands.command(name="anon-addreview", description="Add a review to an existing site thread")
    @app_commands.describe(thread_id="Thread to post in", message="Your review", rating="Star rating 1-5")
    async def addreview(self, interaction: discord.Interaction, thread_id: str, message: str, rating: app_commands.Range[int, 1, 5]):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)

        if thread and isinstance(thread, discord.Thread):
            stars = "⭐" * rating
            sent_msg = await thread.send(f"{stars} - {message}")
            await log_channel.send(
                f"[ANON ADD REVIEW]\nThread: {thread.name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}"
            )
            await interaction.response.send_message("Your anonymous review was posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @app_commands.command(name="anon-question", description="Ask a question anonymously in a thread")
    @app_commands.describe(thread_id="Thread to ask in", message="Your question")
    async def anon_question(self, interaction: discord.Interaction, thread_id: str, message: str):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)

        if thread and isinstance(thread, discord.Thread):
            sent_msg = await thread.send(f"❓ - {message}")
            await log_channel.send(
                f"[ANON QUESTION]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}"
            )
            await interaction.response.send_message("Your anonymous question was posted.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @app_commands.command(name="anon-reply", description="Reply anonymously in a thread to a message")
    @app_commands.describe(thread_id="Thread to reply in", message_id="ID of the message to reply to", message="Your reply")
    async def anon_reply(self, interaction: discord.Interaction, thread_id: str, message_id: str, message: str):
        thread = self.bot.get_channel(int(thread_id))
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)

        if thread and isinstance(thread, discord.Thread):
            try:
                reference_msg = await thread.fetch_message(int(message_id))
                sent_msg = await thread.send(f"↩️ - {message}", reference=reference_msg)
                await log_channel.send(
                    f"[ANON REPLY]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}"
                )
                await interaction.response.send_message("Your anonymous reply was posted.", ephemeral=True)
            except discord.NotFound:
                await interaction.response.send_message("Could not find that message in the thread.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find that thread.", ephemeral=True)

    @addreview.autocomplete("thread_id")
    @anon_question.autocomplete("thread_id")
    @anon_reply.autocomplete("thread_id")
    async def thread_id_autocomplete(self, interaction: discord.Interaction, current: str):
        forum_channel = self.bot.get_channel(FORUM_CHANNEL_ID)
        if not isinstance(forum_channel, discord.ForumChannel):
            return []
        return [
            app_commands.Choice(name=thread.name, value=str(thread.id))
            for thread in forum_channel.threads
            if current.lower() in thread.name.lower()
        ][:25]

    @anon_reply.autocomplete("message_id")
    async def message_id_autocomplete(self, interaction: discord.Interaction, current: str):
        thread_id = interaction.namespace.thread_id
        try:
            thread = self.bot.get_channel(int(thread_id))
        except:
            return []
        if not isinstance(thread, discord.Thread):
            return []
        try:
            messages = [
                message async for message in thread.history(limit=50)
                if current in str(message.id) or current.lower() in message.content.lower()
            ]
        except:
            return []
        return [
            app_commands.Choice(name=f"{m.content[:50]}..." if len(m.content) > 50 else m.content, value=str(m.id))
            for m in messages
        ][:25]


# Button view + modals
class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="newsite_button")
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NewSiteModal())

    @discord.ui.button(label="Add Review", style=discord.ButtonStyle.secondary, custom_id="addreview_button")
    async def addreview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddReviewModal())

    @discord.ui.button(label="Ask Question", style=discord.ButtonStyle.success, custom_id="question_button")
    async def question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuestionModal())

    @discord.ui.button(label="Reply to Message", style=discord.ButtonStyle.danger, custom_id="reply_button")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReplyModal())


class NewSiteModal(discord.ui.Modal, title="Submit New Site Review"):
    site_name = discord.ui.TextInput(label="Site Name", max_length=100)
    message = discord.ui.TextInput(label="Review Message", style=discord.TextStyle.paragraph, max_length=1900)
    rating = discord.ui.TextInput(label="Rating (1-5 stars)", max_length=1)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.client.get_command("anon-newsite").callback(
            interaction, self.site_name.value, self.message.value, int(self.rating.value)
        )


class AddReviewModal(discord.ui.Modal, title="Add Review to Existing Thread"):
    thread_id = discord.ui.TextInput(label="Thread ID")
    message = discord.ui.TextInput(label="Review Message", style=discord.TextStyle.paragraph, max_length=1900)
    rating = discord.ui.TextInput(label="Rating (1-5 stars)", max_length=1)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.client.get_command("anon-addreview").callback(
            interaction, self.thread_id.value, self.message.value, int(self.rating.value)
        )


class QuestionModal(discord.ui.Modal, title="Ask Anonymous Question"):
    thread_id = discord.ui.TextInput(label="Thread ID")
    message = discord.ui.TextInput(label="Your Question", style=discord.TextStyle.paragraph, max_length=1900)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.client.get_command("anon-question").callback(
            interaction, self.thread_id.value, self.message.value
        )


class ReplyModal(discord.ui.Modal, title="Reply Anonymously to Message"):
    thread_id = discord.ui.TextInput(label="Thread ID")
    message_id = discord.ui.TextInput(label="Message ID")
    message = discord.ui.TextInput(label="Your Reply", style=discord.TextStyle.paragraph, max_length=1900)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.client.get_command("anon-reply").callback(
            interaction, self.thread_id.value, self.message_id.value, self.message.value
        )


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
