import discord
from discord import app_commands
from discord.ext import commands
import os

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID"))
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508


class SubmitModal(discord.ui.Modal):
    def __init__(self, command_type: str, thread_id=None, message_id=None):
        self.command_type = command_type
        self.thread_id = thread_id
        self.message_id = message_id

        title_map = {
            "anon-newsite": "Submit New Site Review",
            "anon-addreview": "Review Existing Site",
            "anon-question": "Ask Anonymous Question",
            "anon-reply": "Reply Anonymously to Message",
        }
        super().__init__(title=title_map[command_type])

        if command_type != "anon-newsite":
            # For display only, not editable
            self.add_item(discord.ui.TextInput(label="Thread ID", default=str(thread_id), required=True))
        if command_type == "anon-reply":
            self.add_item(discord.ui.TextInput(label="Message ID to reply to", default=str(message_id or ""), required=True))
        if command_type == "anon-newsite":
            self.add_item(discord.ui.TextInput(label="Site Name", required=True))
        self.add_item(discord.ui.TextInput(label="⭐ Star Rating (1–5 only — required)", required=True))
        self.add_item(discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph))


    async def on_submit(self, interaction: discord.Interaction):
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        forum_channel = interaction.client.get_channel(FORUM_CHANNEL_ID)
        entries = [comp.value for comp in self.children]

        def validate_rating(raw: str) -> tuple[bool, int | None]:
            try:
                val = int(raw)
                if 1 <= val <= 5:
                    return True, val
                return False, None
            except:
                return False, None

        if self.command_type == "anon-newsite":
            site_name, rating_raw, message = entries
            valid, rating = validate_rating(rating_raw)
            if not valid:
                await interaction.response.send_message("❌ Please enter a number between 1 and 5 for the star rating.", ephemeral=True)
                return

            stars = "⭐" * rating
            post_content = f"{stars} - {message}"
            for thread in forum_channel.threads:
                if thread.name.strip().lower() == site_name.strip().lower():
                    sent = await thread.send(post_content)
                    await log_channel.send(f"[ANON REDIRECTED REVIEW]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
                    await interaction.response.send_message(f"Posted to existing thread: {thread.mention}", ephemeral=True)
                    return

            thread = await forum_channel.create_thread(name=site_name, content=post_content)
            starter_message = thread.message
            await log_channel.send(f"[ANON NEW THREAD]\nAuthor: ||{interaction.user}||\n{starter_message.jump_url}")
            await interaction.response.send_message("Posted new site review thread.", ephemeral=True)

        elif self.command_type == "anon-addreview":
            thread_id, rating_raw, message = entries
            valid, rating = validate_rating(rating_raw)
            if not valid:
                await interaction.response.send_message("❌ Please enter a number between 1 and 5 for the star rating.", ephemeral=True)
                return
            thread = interaction.client.get_channel(int(thread_id))
            stars = "⭐" * rating
            sent = await thread.send(f"{stars} - {message}")
            await log_channel.send(f"[ANON ADD REVIEW]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
            await interaction.response.send_message("Review added to thread.", ephemeral=True)

        elif self.command_type == "anon-question":
            thread_id, _, message = entries
            thread = interaction.client.get_channel(int(thread_id))
            sent = await thread.send(f"❓ - {message}")
            await log_channel.send(f"[ANON QUESTION]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
            await interaction.response.send_message("Question posted anonymously.", ephemeral=True)

        elif self.command_type == "anon-reply":
            thread_id, message_id, _, message = entries
            thread = interaction.client.get_channel(int(thread_id))
            ref = await thread.fetch_message(int(message_id))
            sent = await thread.send(f"↩️ - {message}", reference=ref)
            await log_channel.send(f"[ANON REPLY]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
            await interaction.response.send_message("Reply posted anonymously.", ephemeral=True)


class ReviewButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="btn_newsite")
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-newsite"))

    @discord.ui.button(label="Review Existing Site", style=discord.ButtonStyle.primary, custom_id="btn_addreview")
    async def addreview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/anon-addreview` to start and select a thread.", ephemeral=True)

    @discord.ui.button(label="Ask Question", style=discord.ButtonStyle.secondary, custom_id="btn_question")
    async def question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/anon-question` to start and select a thread.", ephemeral=True)

    @discord.ui.button(label="Reply", style=discord.ButtonStyle.secondary, custom_id="btn_reply")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use `/anon-reply` to start and select a thread and message.", ephemeral=True)


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Post the review buttons to the configured channel")
    async def post_buttons(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to run this.", ephemeral=True)
            return
        channel = interaction.client.get_channel(SUBMIT_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Submit channel not found.", ephemeral=True)
            return
        await channel.send("Click a button below to submit anonymously:", view=ReviewButtons(self.bot))
        await interaction.response.send_message("Buttons posted!", ephemeral=True)

    # Autocomplete for thread selection
    @app_commands.command(name="anon-addreview", description="Submit a review to an existing thread")
    @app_commands.describe(thread="Select the thread to review")
    async def anon_addreview(self, interaction: discord.Interaction, thread: discord.Thread):
        await interaction.response.send_modal(SubmitModal("anon-addreview", thread_id=thread.id))

    @app_commands.command(name="anon-question", description="Ask an anonymous question in a thread")
    @app_commands.describe(thread="Select the thread")
    async def anon_question(self, interaction: discord.Interaction, thread: discord.Thread):
        await interaction.response.send_modal(SubmitModal("anon-question", thread_id=thread.id))

    @app_commands.command(name="anon-reply", description="Reply anonymously to a message in a thread")
    @app_commands.describe(thread="Select the thread", message="Select the message ID")
    async def anon_reply(self, interaction: discord.Interaction, thread: discord.Thread, message: discord.Message):
        await interaction.response.send_modal(SubmitModal("anon-reply", thread_id=thread.id, message_id=message.id))

    @anon_addreview.autocomplete('thread')
    @anon_question.autocomplete('thread')
    @anon_reply.autocomplete('thread')
    async def thread_autocomplete(self, interaction: discord.Interaction, current: str):
        forum = interaction.client.get_channel(FORUM_CHANNEL_ID)
        threads = [t for t in forum.threads if current.lower() in t.name.lower()]
        return [app_commands.Choice(name=t.name, value=t.id) for t in threads[:25]]

    @anon_reply.autocomplete('message')
    async def message_autocomplete(self, interaction: discord.Interaction, current: str):
        thread_id = interaction.namespace.thread
        thread = interaction.client.get_channel(thread_id)
        messages = [msg async for msg in thread.history(limit=50) if current.lower() in msg.content.lower()]
        return [app_commands.Choice(name=msg.content[:100], value=msg.id) for msg in messages[:25]]


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
