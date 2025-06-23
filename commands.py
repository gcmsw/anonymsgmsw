import os
import discord
from discord import app_commands
from discord.ext import commands

FORUM_CHANNEL_ID = int(os.getenv("FORUM_CHANNEL_ID", 1384999875237646508))
SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID", 1382563343717502996))

class SubmitModal(discord.ui.Modal, title="Submit New Site Review"):
    site_name = discord.ui.TextInput(label="Site Name", placeholder="Enter the site or organization name")
    star_rating = discord.ui.TextInput(label="Star Rating (1-5)", placeholder="e.g. 4", max_length=1)
    review_body = discord.ui.TextInput(label="Your Review", placeholder="Write your review here", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            stars = int(self.star_rating.value.strip())
            if not (1 <= stars <= 5):
                raise ValueError
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Star Rating",
                description="Please enter a whole number from 1 to 5 for the star rating.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        forum = interaction.guild.get_channel(FORUM_CHANNEL_ID)
        thread = discord.utils.get(forum.threads, name__iexact=self.site_name.value.strip())

        if thread:
            await thread.send(f"{'⭐' * stars} – {self.review_body.value}")
            await interaction.response.send_message(f"✅ Site already exists! Your review was added to **{thread.name}**.", ephemeral=True)
        else:
            thread = await forum.create_thread(name=self.site_name.value.strip(), content=f"{'⭐' * stars} – {self.review_body.value}")
            await interaction.response.send_message(f"✅ Created new site review thread: **{thread.name}**", ephemeral=True)
            await post_help_button(thread)

class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary)
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal())

class HelpButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="How to Post Anonymously", style=discord.ButtonStyle.secondary)
    async def show_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="How to Post Anonymously",
            description="Use the slash commands below to anonymously add reviews, questions, or replies in this thread.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def post_help_button(thread: discord.Thread):
    async for msg in thread.history(limit=50):
        if msg.author.bot and any(btn.label == "How to Post Anonymously" for btn in getattr(msg.components[0], 'children', [])):
            await msg.delete()
    embed = discord.Embed(
        title="How to Post Anonymously",
        description="Use the slash commands below to anonymously add reviews, questions, or replies in this thread.",
        color=discord.Color.blurple()
    )
    await thread.send(embed=embed, view=HelpButtonView())

class ReviewCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.Thread):
            parent = message.channel.parent
            if isinstance(parent, discord.ForumChannel) and parent.id == FORUM_CHANNEL_ID:
                await post_help_button(message.channel)

    @app_commands.command(name="anon-addreview", description="Add an anonymous review to an existing site thread")
    @app_commands.describe(star_rating="1-5 stars", review_body="Your anonymous review")
    async def anon_addreview(self, interaction: discord.Interaction, star_rating: int, review_body: str):
        if not (1 <= star_rating <= 5):
            embed = discord.Embed(
                title="❌ Invalid Star Rating",
                description="Please enter a number between 1 and 5.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("❌ This command must be used inside a forum thread.", ephemeral=True)
            return

        await interaction.channel.send(f"{'⭐' * star_rating} – {review_body}")
        await interaction.response.send_message("✅ Anonymous review posted!", ephemeral=True)
        await post_help_button(interaction.channel)

    @app_commands.command(name="anon-question", description="Ask an anonymous question in a thread")
    @app_commands.describe(question="Your anonymous question")
    async def anon_question(self, interaction: discord.Interaction, question: str):
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("❌ This command must be used inside a forum thread.", ephemeral=True)
            return

        await interaction.channel.send(f"❓ {question}")
        await interaction.response.send_message("✅ Anonymous question posted!", ephemeral=True)
        await post_help_button(interaction.channel)

    @app_commands.command(name="anon-reply", description="Post an anonymous reply to a message in the thread")
    @app_commands.describe(message_link="Right-click 'Copy Message Link' and paste it here", reply="Your anonymous reply")
    async def anon_reply(self, interaction: discord.Interaction, message_link: str, reply: str):
        try:
            parts = message_link.strip().split("/")
            message_id = int(parts[-1])
        except Exception:
            await interaction.response.send_message("❌ Invalid message link format.", ephemeral=True)
            return

        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("❌ This command must be used inside a forum thread.", ephemeral=True)
            return

        try:
            msg = await interaction.channel.fetch_message(message_id)
            await msg.reply(reply)
            await interaction.response.send_message("✅ Anonymous reply posted!", ephemeral=True)
            await post_help_button(interaction.channel)
        except Exception:
            await interaction.response.send_message("❌ Couldn't find or reply to that message.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReviewCog(bot))
