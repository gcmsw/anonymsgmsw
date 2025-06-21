import discord
from discord import app_commands
from discord.ext import commands
import os

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID", 0))

class SubmitModal(discord.ui.Modal):
    def __init__(self, command_type: str, bot: commands.Bot):
        super().__init__(title=self._get_title(command_type))
        self.command_type = command_type
        self.bot = bot

        if command_type != "anon-newsite":
            self.add_item(discord.ui.TextInput(label="Thread ID", required=True))

        if command_type == "anon-reply":
            self.add_item(discord.ui.TextInput(label="Message ID", required=True))

        if command_type == "anon-newsite":
            self.add_item(discord.ui.TextInput(label="Site Name", required=True))

        self.add_item(discord.ui.TextInput(label="Star Rating (1-5)", required=True))
        self.add_item(discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph, required=True))

    def _get_title(self, command_type):
        return {
            "anon-newsite": "Submit New Site Review",
            "anon-addreview": "Review Existing Site",
            "anon-question": "Ask Anonymous Question",
            "anon-reply": "Reply Anonymously to Message",
        }[command_type]

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        forum_channel = self.bot.get_channel(FORUM_CHANNEL_ID)
        entries = [comp.value for comp in self.children]

        try:
            rating = int(entries[-2])
            stars = "⭐" * rating
        except ValueError:
            await interaction.response.send_message("Please enter a number (1-5) for the star rating.", ephemeral=True)
            return

        message = entries[-1]

        if self.command_type == "anon-newsite":
            site_name = entries[0]
            for thread in forum_channel.threads:
                if thread.name.strip().lower() == site_name.strip().lower():
                    sent = await thread.send(f"{stars} - {message}")
                    if log_channel:
                        await log_channel.send(f"[ANON REDIRECTED REVIEW]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
                    await interaction.response.send_message(f"Posted to existing thread: {thread.mention}", ephemeral=True)
                    return
            thread = await forum_channel.create_thread(name=site_name, content=f"{stars} - {message}")
            if log_channel:
                await log_channel.send(f"[ANON NEW THREAD]\nAuthor: ||{interaction.user}||\n{thread.id}")
            await interaction.response.send_message("Posted new site review thread.", ephemeral=True)

        else:
            thread_id = int(entries[0])
            thread = self.bot.get_channel(thread_id)
            if not thread:
                await interaction.response.send_message("Thread not found.", ephemeral=True)
                return

            if self.command_type == "anon-reply":
                message_id = int(entries[1])
                ref = await thread.fetch_message(message_id)
                sent = await thread.send(f"↩️ - {message}", reference=ref)
                if log_channel:
                    await log_channel.send(f"[ANON REPLY]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
                await interaction.response.send_message("Reply posted anonymously.", ephemeral=True)

            elif self.command_type == "anon-addreview":
                sent = await thread.send(f"{stars} - {message}")
                if log_channel:
                    await log_channel.send(f"[ANON ADD REVIEW]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
                await interaction.response.send_message("Review added to thread.", ephemeral=True)

            elif self.command_type == "anon-question":
                sent = await thread.send(f"❓ - {message}")
                if log_channel:
                    await log_channel.send(f"[ANON QUESTION]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
                await interaction.response.send_message("Question posted anonymously.", ephemeral=True)

class ReviewButtons(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="btn_newsite")
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-newsite", self.bot))

    @discord.ui.button(label="Review Existing Site", style=discord.ButtonStyle.primary, custom_id="btn_addreview")
    async def addreview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-addreview", self.bot))

    @discord.ui.button(label="Ask Question", style=discord.ButtonStyle.secondary, custom_id="btn_question")
    async def question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-question", self.bot))

    @discord.ui.button(label="Reply", style=discord.ButtonStyle.secondary, custom_id="btn_reply")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-reply", self.bot))

class CommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Post the review buttons to the configured channel")
    async def post_buttons(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to run this.", ephemeral=True)
            return
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if not channel:
            await interaction.response.send_message("Submit channel not found.", ephemeral=True)
            return
        await channel.send("Click a button below to submit anonymously:", view=ReviewButtons(self.bot))
        await interaction.response.send_message("Buttons posted!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
