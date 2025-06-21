import discord
from discord import app_commands
from discord.ext import commands
import os

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID"))
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508


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

        self.add_item(discord.ui.TextInput(label="Thread ID (for all but newsite)", required=False))
        if command_type == "anon-reply":
            self.add_item(discord.ui.TextInput(label="Message ID to reply to"))
        if command_type == "anon-newsite":
            self.add_item(discord.ui.TextInput(label="Site Name"))
        self.add_item(discord.ui.TextInput(label="Star Rating (1-5)", required=False))
        self.add_item(discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
        forum_channel = interaction.client.get_channel(FORUM_CHANNEL_ID)
        entries = [comp.value for comp in self.children]

        if self.command_type == "anon-newsite":
            _, site_name, rating, message = entries
            stars = "⭐" * int(rating)
            post_content = f"{stars} - {message}"
            for thread in forum_channel.threads:
                if thread.name.strip().lower() == site_name.strip().lower():
                    sent = await thread.send(post_content)
                    await log_channel.send(f"[ANON REDIRECTED REVIEW]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
                    await interaction.response.send_message(f"Posted to existing thread: {thread.mention}", ephemeral=True)
                    return
            thread = await forum_channel.create_thread(name=site_name, content=post_content)
            await log_channel.send(f"[ANON NEW THREAD]\nAuthor: ||{interaction.user}||\n{thread.jump_url}")
            await interaction.response.send_message("Posted new site review thread.", ephemeral=True)

        elif self.command_type == "anon-addreview":
            thread_id, _, rating, message = entries
            thread = interaction.client.get_channel(int(thread_id))
            stars = "⭐" * int(rating)
            sent = await thread.send(f"{stars} - {message}")
            await log_channel.send(f"[ANON ADD REVIEW]\nAuthor: ||{interaction.user}||\n{sent.jump_url}")
            await interaction.response.send_message("Review added to thread.", ephemeral=True)

        elif self.command_type == "anon-question":
            thread_id, _, _, message = entries
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
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="btn_newsite")
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-newsite"))

    @discord.ui.button(label="Add Review", style=discord.ButtonStyle.primary, custom_id="btn_addreview")
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


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
