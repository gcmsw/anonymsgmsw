import discord
from discord.ext import commands
from discord import app_commands
import os

LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508

class SubmitModal(discord.ui.Modal):
    def __init__(self, command_name: str):
        super().__init__(title="Anonymous Submission")
        self.command_name = command_name

        if command_name == "anon-newsite":
            self.add_item(discord.ui.TextInput(label="Site Name", custom_id="site_name", max_length=100))
            self.add_item(discord.ui.TextInput(label="Message", custom_id="message", style=discord.TextStyle.paragraph, max_length=1900))
            self.add_item(discord.ui.TextInput(label="Rating (1-5)", custom_id="rating", max_length=1))
        elif command_name in ["anon-addreview", "anon-question"]:
            self.add_item(discord.ui.TextInput(label="Thread ID", custom_id="thread_id", max_length=25))
            self.add_item(discord.ui.TextInput(label="Message", custom_id="message", style=discord.TextStyle.paragraph, max_length=1900))
            if command_name == "anon-addreview":
                self.add_item(discord.ui.TextInput(label="Rating (1-5)", custom_id="rating", max_length=1))
        elif command_name == "anon-reply":
            self.add_item(discord.ui.TextInput(label="Thread ID", custom_id="thread_id", max_length=25))
            self.add_item(discord.ui.TextInput(label="Message ID to Reply To", custom_id="message_id", max_length=25))
            self.add_item(discord.ui.TextInput(label="Message", custom_id="message", style=discord.TextStyle.paragraph, max_length=1900))

    async def on_submit(self, interaction: discord.Interaction):
        bot = interaction.client
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        forum_channel = bot.get_channel(FORUM_CHANNEL_ID)

        try:
            if self.command_name == "anon-newsite":
                site_name = self.children[0].value
                message = self.children[1].value
                rating = int(self.children[2].value)
                stars = "⭐" * rating
                post_content = f"{stars} - {message}"

                for thread in forum_channel.threads:
                    if thread.name.strip().lower() == site_name.strip().lower():
                        sent_msg = await thread.send(post_content)
                        await log_channel.send(f"[ANON REDIRECTED REVIEW]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nThread: {sent_msg.jump_url}")
                        await interaction.response.send_message(f"Posted to existing thread: {thread.mention}", ephemeral=True)
                        return

                thread = await forum_channel.create_thread(name=site_name, content=post_content)
                await log_channel.send(f"[ANON NEW THREAD]\nSite: {site_name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nThread: {thread.jump_url}")
                await interaction.response.send_message("Your anonymous review has been submitted.", ephemeral=True)

            elif self.command_name == "anon-addreview":
                thread_id = int(self.children[0].value)
                message = self.children[1].value
                rating = int(self.children[2].value)
                thread = bot.get_channel(thread_id)
                if thread and isinstance(thread, discord.Thread):
                    stars = "⭐" * rating
                    sent_msg = await thread.send(f"{stars} - {message}")
                    await log_channel.send(f"[ANON ADD REVIEW]\nThread: {thread.name}\nRating: {rating}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
                    await interaction.response.send_message("Your anonymous review was posted.", ephemeral=True)
                else:
                    await interaction.response.send_message("Could not find that thread.", ephemeral=True)

            elif self.command_name == "anon-question":
                thread_id = int(self.children[0].value)
                message = self.children[1].value
                thread = bot.get_channel(thread_id)
                if thread and isinstance(thread, discord.Thread):
                    sent_msg = await thread.send(f"❓ - {message}")
                    await log_channel.send(f"[ANON QUESTION]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
                    await interaction.response.send_message("Your anonymous question was posted.", ephemeral=True)
                else:
                    await interaction.response.send_message("Could not find that thread.", ephemeral=True)

            elif self.command_name == "anon-reply":
                thread_id = int(self.children[0].value)
                message_id = int(self.children[1].value)
                message = self.children[2].value
                thread = bot.get_channel(thread_id)
                if thread and isinstance(thread, discord.Thread):
                    reference_msg = await thread.fetch_message(message_id)
                    sent_msg = await thread.send(f"↩️ - {message}", reference=reference_msg)
                    await log_channel.send(f"[ANON REPLY]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nMessage: {message}\nMessage: {sent_msg.jump_url}")
                    await interaction.response.send_message("Your anonymous reply was posted.", ephemeral=True)
                else:
                    await interaction.response.send_message("Could not find that thread or message.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Post the anonymous button panel.")
    async def post_buttons(self, interaction: discord.Interaction):
        submit_channel_id = int(os.getenv("SUBMIT_CHANNEL_ID"))
        channel = self.bot.get_channel(submit_channel_id)
        if not channel:
            await interaction.response.send_message("Submit channel not found.", ephemeral=True)
            return
        await channel.send("Click a button below to submit anonymously:", view=ReviewButtons())
        await interaction.response.send_message("✅ Button panel posted.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
