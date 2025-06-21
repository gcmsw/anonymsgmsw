import discord
from discord.ext import commands
from discord import app_commands
import os

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID", 0))
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508


class SubmitModal(discord.ui.Modal):
    def __init__(self, command_type: str):
        super().__init__(title="Submit Anonymously")
        self.command_type = command_type

        self.add_item(discord.ui.TextInput(label="Your Message", style=discord.TextStyle.paragraph, required=True, max_length=1900))

        if command_type in ["anon-newsite", "anon-addreview"]:
            self.add_item(discord.ui.TextInput(label="Star Rating (1-5)", placeholder="e.g., 5", required=True, max_length=1))
        if command_type in ["anon-addreview", "anon-question", "anon-reply"]:
            self.add_item(discord.ui.TextInput(label="Thread ID", placeholder="Paste the thread ID", required=True))
        if command_type == "anon-reply":
            self.add_item(discord.ui.TextInput(label="Message ID", placeholder="Paste the message ID", required=True))

    async def on_submit(self, interaction: discord.Interaction):
        bot = interaction.client
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        forum_channel = bot.get_channel(FORUM_CHANNEL_ID)

        try:
            if self.command_type == "anon-newsite":
                site_name = "Anonymous Site"
                message = self.children[0].value
                rating = int(self.children[1].value)
                stars = "⭐" * rating
                post_content = f"{stars} - {message}"

                for thread in forum_channel.threads:
                    if thread.name.lower() == site_name.lower():
                        sent_msg = await thread.send(post_content)
                        await log_channel.send(f"[ANON REDIRECTED REVIEW]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nThread: {sent_msg.jump_url}")
                        await interaction.response.send_message(f"Review added to existing thread: {thread.mention}", ephemeral=True)
                        return

                thread = await forum_channel.create_thread(name=site_name, content=post_content)
                await log_channel.send(f"[ANON NEW THREAD]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nThread: {thread.message.jump_url}")
                await interaction.response.send_message("New site review submitted.", ephemeral=True)

            elif self.command_type == "anon-addreview":
                message = self.children[0].value
                rating = int(self.children[1].value)
                thread_id = int(self.children[2].value)
                thread = bot.get_channel(thread_id)

                if thread and isinstance(thread, discord.Thread):
                    stars = "⭐" * rating
                    sent_msg = await thread.send(f"{stars} - {message}")
                    await log_channel.send(f"[ANON ADD REVIEW]\nThread: {thread.name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
                    await interaction.response.send_message("Review added to thread.", ephemeral=True)
                else:
                    await interaction.response.send_message("Thread not found.", ephemeral=True)

            elif self.command_type == "anon-question":
                message = self.children[0].value
                thread_id = int(self.children[1].value)
                thread = bot.get_channel(thread_id)

                if thread and isinstance(thread, discord.Thread):
                    sent_msg = await thread.send(f"❓ - {message}")
                    await log_channel.send(f"[ANON QUESTION]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
                    await interaction.response.send_message("Question posted anonymously.", ephemeral=True)
                else:
                    await interaction.response.send_message("Thread not found.", ephemeral=True)

            elif self.command_type == "anon-reply":
                message = self.children[0].value
                thread_id = int(self.children[1].value)
                message_id = int(self.children[2].value)
                thread = bot.get_channel(thread_id)

                if thread and isinstance(thread, discord.Thread):
                    try:
                        ref_msg = await thread.fetch_message(message_id)
                        sent_msg = await thread.send(f"↩️ - {message}", reference=ref_msg)
                        await log_channel.send(f"[ANON REPLY]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
                        await interaction.response.send_message("Reply posted anonymously.", ephemeral=True)
                    except discord.NotFound:
                        await interaction.response.send_message("Referenced message not found.", ephemeral=True)
                else:
                    await interaction.response.send_message("Thread not found.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Something went wrong: {e}", ephemeral=True)


class ReviewButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary)
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-newsite"))

    @discord.ui.button(label="Add to Site Thread", style=discord.ButtonStyle.success)
    async def addreview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-addreview"))

    @discord.ui.button(label="Ask a Question", style=discord.ButtonStyle.secondary)
    async def question_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-question"))

    @discord.ui.button(label="Reply to Message", style=discord.ButtonStyle.danger)
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal("anon-reply"))


class ButtonCommandCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Post the anonymous submission button panel.")
    async def post_buttons(self, interaction: discord.Interaction):
        if interaction.channel.id != SUBMIT_CHANNEL_ID:
            await interaction.response.send_message("This command can only be used in the designated channel.", ephemeral=True)
            return
        await interaction.response.send_message("✅ Button panel posted.", ephemeral=True)
        await interaction.channel.send(
            "Click a button below to submit anonymously:",
            view=ReviewButtons(self.bot)
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ButtonCommandCog(bot))
