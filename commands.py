import os
import discord
from discord.ext import commands
from discord import app_commands

SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID", 0))
LOG_CHANNEL_ID = 1382563380367331429
FORUM_CHANNEL_ID = 1384999875237646508

class SubmitModal(discord.ui.Modal):
    def __init__(self, bot, command_type):
        self.bot = bot
        self.command_type = command_type
        title_map = {
            "anon-newsite": "Submit New Site Review",
            "anon-addreview": "Add to Site Thread",
            "anon-question": "Ask a Question",
            "anon-reply": "Reply to Message"
        }
        super().__init__(title=title_map[command_type])

        # Inputs per command
        if command_type == "anon-newsite":
            self.site = discord.ui.TextInput(label="Site Name", required=True)
            self.review = discord.ui.TextInput(label="Review", style=discord.TextStyle.paragraph, required=True)
            self.rating = discord.ui.TextInput(label="Rating (1–5)", required=True)
            self.add_item(self.site)
            self.add_item(self.review)
            self.add_item(self.rating)

        elif command_type == "anon-addreview":
            self.thread_id = discord.ui.TextInput(label="Thread ID", required=True)
            self.review = discord.ui.TextInput(label="Review", style=discord.TextStyle.paragraph, required=True)
            self.rating = discord.ui.TextInput(label="Rating (1–5)", required=True)
            self.add_item(self.thread_id)
            self.add_item(self.review)
            self.add_item(self.rating)

        elif command_type == "anon-question":
            self.thread_id = discord.ui.TextInput(label="Thread ID", required=True)
            self.question = discord.ui.TextInput(label="Your Question", style=discord.TextStyle.paragraph, required=True)
            self.add_item(self.thread_id)
            self.add_item(self.question)

        elif command_type == "anon-reply":
            self.thread_id = discord.ui.TextInput(label="Thread ID", required=True)
            self.message_id = discord.ui.TextInput(label="Message ID", required=True)
            self.reply = discord.ui.TextInput(label="Your Reply", style=discord.TextStyle.paragraph, required=True)
            self.add_item(self.thread_id)
            self.add_item(self.message_id)
            self.add_item(self.reply)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = self.bot.get_channel(LOG_CHANNEL_ID)
        forum_channel = self.bot.get_channel(FORUM_CHANNEL_ID)

        try:
            if self.command_type == "anon-newsite":
                stars = "⭐" * int(self.rating.value)
                for thread in forum_channel.threads:
                    if thread.name.lower() == self.site.value.lower():
                        msg = await thread.send(f"{stars} - {self.review.value}")
                        await log_channel.send(f"[ANON REDIRECTED REVIEW]\nSite: {self.site.value}\nRating: {self.rating.value}\nAuthor: ||{interaction.user}||\nMessage: {self.review.value}\nThread: {msg.jump_url}")
                        await interaction.response.send_message(f"✅ Posted to existing thread: {thread.mention}", ephemeral=True)
                        return
                thread = await forum_channel.create_thread(name=self.site.value, content=f"{stars} - {self.review.value}")
                await log_channel.send(f"[ANON NEW THREAD]\nSite: {self.site.value}\nRating: {self.rating.value}\nAuthor: ||{interaction.user}||\nMessage: {self.review.value}\nThread: {thread.jump_url}")
                await interaction.response.send_message("✅ Posted and new thread created.", ephemeral=True)

            elif self.command_type == "anon-addreview":
                thread = self.bot.get_channel(int(self.thread_id.value))
                stars = "⭐" * int(self.rating.value)
                msg = await thread.send(f"{stars} - {self.review.value}")
                await log_channel.send(f"[ANON ADD REVIEW]\nThread: {thread.name}\nRating: {self.rating.value}\nAuthor: ||{interaction.user}||\nMessage: {self.review.value}\nLink: {msg.jump_url}")
                await interaction.response.send_message("✅ Review added.", ephemeral=True)

            elif self.command_type == "anon-question":
                thread = self.bot.get_channel(int(self.thread_id.value))
                msg = await thread.send(f"❓ - {self.question.value}")
                await log_channel.send(f"[ANON QUESTION]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nQuestion: {self.question.value}\nLink: {msg.jump_url}")
                await interaction.response.send_message("✅ Question posted.", ephemeral=True)

            elif self.command_type == "anon-reply":
                thread = self.bot.get_channel(int(self.thread_id.value))
                msg_ref = await thread.fetch_message(int(self.message_id.value))
                msg = await thread.send(f"↩️ - {self.reply.value}", reference=msg_ref)
                await log_channel.send(f"[ANON REPLY]\nThread: {thread.name}\nAuthor: ||{interaction.user}||\nReply: {self.reply.value}\nLink: {msg.jump_url}")
                await interaction.response.send_message("✅ Reply posted.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ Something went wrong: {e}", ephemeral=True)


class ReviewButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary)
    async def newsite(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal(self.bot, "anon-newsite"))

    @discord.ui.button(label="Add to Site Thread", style=discord.ButtonStyle.success)
    async def addreview(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal(self.bot, "anon-addreview"))

    @discord.ui.button(label="Ask a Question", style=discord.ButtonStyle.secondary)
    async def ask(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal(self.bot, "anon-question"))

    @discord.ui.button(label="Reply to Message", style=discord.ButtonStyle.danger)
    async def reply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal(self.bot, "anon-reply"))


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Manually post the anonymous submission button panel.")
    async def post_buttons(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if channel:
            await channel.send("Click a button below to submit anonymously:", view=ReviewButtons(self.bot))
            await interaction.response.send_message("✅ Button panel posted.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Could not find the submit channel.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
