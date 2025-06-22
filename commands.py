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
    def __init__(self, command_type: str, prefill_data: dict = None):
        self.command_type = command_type
        self.prefill_data = prefill_data or {}
        title_map = {
            "anon-newsite": "Submit New Site Review",
            "anon-help": "How to Post Anonymously"
        }
        super().__init__(title=title_map[command_type])

        if command_type == "anon-newsite":
            self.add_item(discord.ui.TextInput(
                label="Site Name",
                placeholder="Name of the field site you're reviewing",
                required=True
            ))
            self.add_item(discord.ui.TextInput(
                label="Star Rating (1-5)",
                placeholder="Enter a number from 1 to 5",
                required=True
            ))
            self.add_item(discord.ui.TextInput(
                label="Message",
                placeholder="What do you want to say?",
                style=discord.TextStyle.paragraph
            ))

        elif command_type == "anon-help":
            self.add_item(discord.ui.TextInput(
                label="How to Use Slash Commands",
                default="Use /anon-addreview to add to an existing site, /anon-question to ask anonymously, and /anon-reply to respond to a message. Start typing the thread or message content to use autocomplete.",
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=400
            ))

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

            elif self.command_type == "anon-help":
                await interaction.response.send_message("Slash command guide displayed.", ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Please enter a valid number (1-5) for the star rating.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong: {e}", ephemeral=True)

class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit New Site Review", style=discord.ButtonStyle.primary, custom_id="btn_newsite")
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-newsite"))

class HelpButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="How to Post Anonymously", style=discord.ButtonStyle.secondary, custom_id="btn_help")
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-help"))

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Post the review or help buttons")
    @app_commands.describe(context="Where to post the button set")
    async def post_buttons(self, interaction: discord.Interaction, context: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to run this.", ephemeral=True)
            return

        if context == "submit":
            channel = interaction.client.get_channel(SUBMIT_CHANNEL_ID)
            if channel:
                await channel.send("Click to submit a new site review:", view=ReviewButtons())
        elif context == "thread":
            if isinstance(interaction.channel, discord.Thread):
                await interaction.channel.send("Need help posting anonymously?", view=HelpButton())
        await interaction.response.send_message("Button(s) posted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
