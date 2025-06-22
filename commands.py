import discord
from discord import app_commands
from discord.ext import commands
import os

SUBMIT_CHANNEL_ID = int(os.environ["SUBMIT_CHANNEL_ID"])
FORUM_CHANNEL_ID = int(os.environ["FORUM_CHANNEL_ID"])
GUILD_ID = discord.Object(id=int(os.environ["GUILD_ID"]))


class SubmitModal(discord.ui.Modal, title="Submit New Site Review"):
    site_name = discord.ui.TextInput(label="Site Name", placeholder="e.g. Asian Health Services", required=True)
    review = discord.ui.TextInput(label="Your Review", style=discord.TextStyle.paragraph, required=True)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        forum = interaction.guild.get_channel(FORUM_CHANNEL_ID)
        existing_thread = None

        for thread in forum.threads:
            if thread.name.lower() == self.site_name.value.strip().lower():
                existing_thread = thread
                break

        if existing_thread:
            await existing_thread.send(f"📝 Anonymous Review:\n{self.review.value}")
            await interaction.response.send_message(
                f"✅ Your review was added to the existing thread: {existing_thread.mention}",
                ephemeral=True
            )
            await post_help_button(existing_thread, self.bot)
        else:
            thread = await forum.create_thread(
                name=self.site_name.value.strip(),
                content=f"📝 Anonymous Review:\n{self.review.value}"
            )
            await interaction.response.send_message(f"✅ New thread created for **{thread.name}**.", ephemeral=True)
            await post_help_button(thread, self.bot)


class ReviewButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Submit New Site Review", style=discord.ButtonStyle.primary, custom_id="submit_new_site_review")
    async def submit_review(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal(self.bot))


async def post_help_button(thread: discord.Thread, bot):
    async for message in thread.history(limit=50, oldest_first=False):
        if message.author == bot.user and message.components:
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


class AnonBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anon-addreview", description="Post an anonymous review to a field site thread")
    @app_commands.describe(thread="Select the site thread", review="Your anonymous review")
    async def anon_addreview(self, interaction: discord.Interaction, thread: str, review: str):
        thread_obj = await interaction.guild.fetch_channel(int(thread))
        await thread_obj.send(f"📝 Anonymous Review:\n{review}")
        await interaction.response.send_message("✅ Your anonymous review was posted.", ephemeral=True)
        await post_help_button(thread_obj, self.bot)

    @app_commands.command(name="anon-question", description="Post an anonymous question to a site thread")
    @app_commands.describe(thread="Select the site thread", question="Your anonymous question")
    async def anon_question(self, interaction: discord.Interaction, thread: str, question: str):
        thread_obj = await interaction.guild.fetch_channel(int(thread))
        await thread_obj.send(f"❓ Anonymous Question:\n{question}")
        await interaction.response.send_message("✅ Your anonymous question was posted.", ephemeral=True)
        await post_help_button(thread_obj, self.bot)

    @app_commands.command(name="anon-reply", description="Reply anonymously to a specific message in a thread")
    @app_commands.describe(thread="Select the site thread", message_id="ID of the message to reply to", reply="Your reply")
    async def anon_reply(self, interaction: discord.Interaction, thread: str, message_id: str, reply: str):
        try:
            thread_obj = await interaction.guild.fetch_channel(int(thread))
            message = await thread_obj.fetch_message(int(message_id))
            await message.reply(f"💬 Anonymous Reply:\n{reply}")
            await interaction.response.send_message("✅ Your anonymous reply was posted.", ephemeral=True)
            await post_help_button(thread_obj, self.bot)
        except:
            await interaction.response.send_message("⚠️ Could not find the message. Please check the ID.", ephemeral=True)

    @app_commands.command(name="post-buttons", description="Manually post the Submit New Site Review button.")
    async def post_buttons(self, interaction: discord.Interaction):
        submit_channel = interaction.guild.get_channel(SUBMIT_CHANNEL_ID)
        if not submit_channel:
            await interaction.response.send_message("❌ Submit channel not found.", ephemeral=True)
            return

        await submit_channel.send(
            "📝 Click the button below to submit a new site review:",
            view=ReviewButtons(self.bot)
        )
        await interaction.response.send_message("✅ Submit button posted.", ephemeral=True)

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
        thread_id = interaction.namespace.thread
        if not thread_id:
            return []
        try:
            thread_obj = await interaction.guild.fetch_channel(int(thread_id))
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
            return
        await post_help_button(message.channel, self.bot)


async def setup(bot):
    await bot.add_cog(AnonBot(bot))
    print("✅ AnonBot loaded successfully.")
