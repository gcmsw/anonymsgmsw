import discord
from discord import app_commands
from discord.ext import commands
import os

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID"))
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508

# Autocomplete functions
async def thread_autocomplete(interaction: discord.Interaction, current: str):
    try:
        forum = interaction.client.get_channel(FORUM_CHANNEL_ID)
        if not forum:
            return []
        return [
            app_commands.Choice(name=thread.name, value=str(thread.id))
            for thread in forum.threads
            if current.lower() in thread.name.lower()
        ][:25]
    except Exception:
        return []

async def message_autocomplete(interaction: discord.Interaction, current: str):
    thread_id = getattr(interaction.namespace, "thread_id", None)
    if not thread_id or not thread_id.isdigit():
        return []
    try:
        thread = interaction.client.get_channel(int(thread_id))
        if not thread:
            return []
        messages = [msg async for msg in thread.history(limit=100)]
        return [
            app_commands.Choice(name=msg.content[:50], value=str(msg.id))
            for msg in messages if current.lower() in msg.content.lower()
        ][:25]
    except Exception:
        return []

class SubmitModal(discord.ui.Modal):
    def __init__(self, command_type: str):
        self.command_type = command_type
        title_map = {
            "anon-newsite": "Submit New Site Review",
            "anon-addreview": "Add Review to Existing Site",
            "anon-question": "Ask Anonymous Question",
            "anon-reply": "Reply Anonymously to Message",
        }
        super().__init__(title=title_map[command_type])

        if command_type != "anon-newsite":
            self.add_item(discord.ui.TextInput(label="Thread ID", placeholder="Paste the Thread ID (from slash autocomplete)", required=True))
        if command_type == "anon-reply":
            self.add_item(discord.ui.TextInput(label="Message ID to reply to", placeholder="Paste the Message ID to reply to", required=True))
        if command_type == "anon-newsite":
            self.add_item(discord.ui.TextInput(label="Site Name", placeholder="Name of the field site you're reviewing", required=True))
        if command_type in ("anon-newsite", "anon-addreview"):
            self.add_item(discord.ui.TextInput(label="Star Rating (1-5)", placeholder="Enter a number from 1 to 5", required=True))
        self.add_item(discord.ui.TextInput(label="Message", placeholder="What do you want to say?", style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
            forum_channel = interaction.client.get_channel(FORUM_CHANNEL_ID)
            entries = [comp.value for comp in self.children]

            if self.command_type == "anon-newsite":
                site_name, rating, message = entries
                rating_int = int(rating)
                stars = "⭐" * rating_int
                for thread in forum_channel.threads:
                    if thread.name.strip().lower() == site_name.strip().lower():
                        sent = await thread.send(f"{stars} - {message}")
                        await log_channel.send(f"[ANON REDIRECTED REVIEW]\nAuthor: ||{interaction.user}||\nContent: {stars} - {message}\nLink: {sent.jump_url}")
                        await interaction.response.send_message(f"Posted to existing thread: {thread.mention}", ephemeral=True)
                        return
                thread = await forum_channel.create_thread(name=site_name, content=f"{stars} - {message}")
                await log_channel.send(f"[ANON NEW THREAD]\nAuthor: ||{interaction.user}||\nContent: {stars} - {message}\nLink: https://discord.com/channels/{forum_channel.guild.id}/{thread.id}")
                await interaction.response.send_message("Posted new site review thread.", ephemeral=True)

            elif self.command_type == "anon-addreview":
                thread_id, rating, message = entries
                thread = interaction.client.get_channel(int(thread_id))
                rating_int = int(rating)
                stars = "⭐" * rating_int
                sent = await thread.send(f"{stars} - {message}")
                await log_channel.send(f"[ANON ADD REVIEW]\nAuthor: ||{interaction.user}||\nContent: {stars} - {message}\nLink: {sent.jump_url}")
                await interaction.response.send_message("Review added to thread.", ephemeral=True)

            elif self.command_type == "anon-question":
                thread_id, message = entries
                thread = interaction.client.get_channel(int(thread_id))
                sent = await thread.send(f"❓ - {message}")
                await log_channel.send(f"[ANON QUESTION]\nAuthor: ||{interaction.user}||\nContent: ❓ - {message}\nLink: {sent.jump_url}")
                await interaction.response.send_message("Question posted anonymously.", ephemeral=True)

            elif self.command_type == "anon-reply":
                thread_id, message_id, message = entries
                thread = interaction.client.get_channel(int(thread_id))
                ref = await thread.fetch_message(int(message_id))
                sent = await thread.send(f"↩️ - {message}", reference=ref)
                await log_channel.send(f"[ANON REPLY]\nAuthor: ||{interaction.user}||\nContent: ↩️ - {message}\nLink: {sent.jump_url}")
                await interaction.response.send_message("Reply posted anonymously.", ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Please enter a valid number (1-5) for the star rating.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong: {e}", ephemeral=True)

class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="btn_newsite")
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-newsite"))

    @discord.ui.button(label="Review Existing Site", style=discord.ButtonStyle.primary, custom_id="btn_addreview")
    async def addreview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-addreview"))

    @discord.ui.button(label="Ask Question", style=discord.ButtonStyle.secondary, custom_id="btn_question")
    async def question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-question"))

    @discord.ui.button(label="Reply", style=discord.ButtonStyle.secondary, custom_id="btn_reply")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-reply"))

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
        await channel.send("Click a button below to submit anonymously:", view=ReviewButtons())
        await interaction.response.send_message("Buttons posted!", ephemeral=True)

    @app_commands.command(name="anon-reply", description="Reply anonymously to a message")
    @app_commands.describe(thread_id="Thread ID", message_id="Message ID")
    @app_commands.autocomplete(thread_id=thread_autocomplete, message_id=message_autocomplete)
    async def anon_reply(self, interaction: discord.Interaction, thread_id: str, message_id: str):
        await interaction.response.send_modal(SubmitModal("anon-reply"))

    @app_commands.command(name="anon-addreview", description="Add review to existing site")
    @app_commands.describe(thread_id="Thread ID")
    @app_commands.autocomplete(thread_id=thread_autocomplete)
    async def anon_addreview(self, interaction: discord.Interaction, thread_id: str):
        await interaction.response.send_modal(SubmitModal("anon-addreview"))

    @app_commands.command(name="anon-question", description="Ask an anonymous question in a thread")
    @app_commands.describe(thread_id="Thread ID")
    @app_commands.autocomplete(thread_id=thread_autocomplete)
    async def anon_question(self, interaction: discord.Interaction, thread_id: str):
        await interaction.response.send_modal(SubmitModal("anon-question"))

    @app_commands.command(name="anon-newsite", description="Create a new site thread with initial review")
    async def anon_newsite(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SubmitModal("anon-newsite"))

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
