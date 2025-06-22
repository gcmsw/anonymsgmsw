import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
import os

GUILD_ID = discord.Object(id=YOUR_GUILD_ID_HERE)  # Replace with actual guild ID
SUBMIT_CHANNEL_ID = 1382563343717502996
FORUM_CHANNEL_ID = 1384999875237646508
LOG_CHANNEL_ID = YOUR_LOG_CHANNEL_ID  # Optional: logging channel

class AnonBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_help_button(self, thread: discord.Thread):
        # Delete old help buttons
        async for message in thread.history(limit=50, oldest_first=False):
            if message.author == self.bot.user and message.components:
                await message.delete()
                break

        embed = discord.Embed(
            title="📢 Post Anonymously",
            description="To post anonymously in this thread:\n• Use `/anon-question`, `/anon-reply`, or `/anon-addreview`\n• Your identity will be hidden\n\nIf you're unsure, just click the slash command bar below and start typing!",
            color=discord.Color.blue()
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Learn how to post anonymously", style=discord.ButtonStyle.secondary, disabled=True))

        await thread.send(embed=embed, view=view)

    async def post_to_forum(self, interaction, site_name, review_text):
        forum = interaction.guild.get_channel(FORUM_CHANNEL_ID)
        thread = None

        for t in forum.threads:
            if t.name.lower() == site_name.lower():
                thread = t
                break

        if not thread:
            thread = await forum.create_thread(name=site_name, content=review_text)
            await interaction.response.send_message(f"✅ New thread created for **{site_name}**.", ephemeral=True)
        else:
            await thread.send(review_text)
            await interaction.response.send_message(
                f"📌 Your review was added to the existing thread: {thread.mention}", ephemeral=True
            )

        await self.ensure_help_button(thread)

    @app_commands.command(name="anon-addreview", description="Post an anonymous review to a field site thread")
    @app_commands.describe(thread="Select the site thread", review="Your anonymous review")
    async def anon_addreview(self, interaction: discord.Interaction, thread: discord.Thread, review: str):
        await thread.send(f"📝 Anonymous Review:\n{review}")
        await interaction.response.send_message("✅ Your anonymous review was posted.", ephemeral=True)
        await self.ensure_help_button(thread)

    @app_commands.command(name="anon-question", description="Post an anonymous question to a site thread")
    @app_commands.describe(thread="Select the site thread", question="Your anonymous question")
    async def anon_question(self, interaction: discord.Interaction, thread: discord.Thread, question: str):
        await thread.send(f"❓ Anonymous Question:\n{question}")
        await interaction.response.send_message("✅ Your anonymous question was posted.", ephemeral=True)
        await self.ensure_help_button(thread)

    @app_commands.command(name="anon-reply", description="Reply anonymously to a specific message in a thread")
    @app_commands.describe(thread="Select the site thread", message_id="ID of the message to reply to", reply="Your reply")
    async def anon_reply(self, interaction: discord.Interaction, thread: discord.Thread, message_id: str, reply: str):
        try:
            message = await thread.fetch_message(int(message_id))
            await message.reply(f"💬 Anonymous Reply:\n{reply}")
            await interaction.response.send_message("✅ Your anonymous reply was posted.", ephemeral=True)
            await self.ensure_help_button(thread)
        except:
            await interaction.response.send_message("⚠️ Could not find the message. Please check the ID.", ephemeral=True)

    @anon_addreview.autocomplete("thread")
    @anon_question.autocomplete("thread")
    @anon_reply.autocomplete("thread")
    async def autocomplete_threads(self, interaction: discord.Interaction, current: str):
        forum = interaction.guild.get_channel(FORUM_CHANNEL_ID)
        return [
            app_commands.Choice(name=thread.name, value=str(thread.id))
            for thread in forum.threads
            if current.lower() in thread.name.lower()
        ][:25]

    @anon_reply.autocomplete("message_id")
    async def autocomplete_message_id(self, interaction: discord.Interaction, current: str):
        thread = interaction.namespace.thread
        if not thread:
            return []
        try:
            thread_obj = await interaction.guild.fetch_channel(int(thread.id))
            messages = [msg async for msg in thread_obj.history(limit=50)]
            return [
                app_commands.Choice(name=f"{m.author.display_name}: {m.content[:30]}", value=str(m.id))
                for m in messages if current in str(m.id)
            ][:25]
        except:
            return []

    @commands.Cog.listener()
    async def on_message(self, message):
        if not isinstance(message.channel, discord.Thread):
            return
        if message.channel.parent_id != FORUM_CHANNEL_ID:
            return
        if message.author.bot:
            return  # Already handled elsewhere

        await self.ensure_help_button(message.channel)


async def setup(bot):
    await bot.add_cog(AnonBot(bot))
