import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

FIELD_FORUM_CHANNEL_ID = int(os.getenv("FIELD_FORUM_CHANNEL_ID"))
HELP_BUTTON_LABEL = "How to Post Anonymously"

class ReviewButtons(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.add_item(Button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="newsite_button"))

    @discord.ui.button(label="New Site Review", style=discord.ButtonStyle.primary, custom_id="newsite_button")
    async def newsite_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please use `/anon-newsite` to post your review.", ephemeral=True)

class HelpButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label=HELP_BUTTON_LABEL, style=discord.ButtonStyle.secondary))

async def post_help_button(thread: discord.Thread):
    try:
        async for msg in thread.history(limit=50):
            if msg.author.bot and msg.components and any(btn.label == HELP_BUTTON_LABEL for btn in getattr(msg.components[0], 'children', [])):
                await msg.delete()
        embed = discord.Embed(
            title="How to Post Anonymously",
            description="Use the slash commands below to anonymously add reviews, questions, or replies in this thread.",
            color=discord.Color.blurple()
        )
        await thread.send(embed=embed, view=HelpButtonView())
    except Exception as e:
        print(f"Error posting help button: {e}")

class ReviewCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.Thread) and message.channel.parent_id == FIELD_FORUM_CHANNEL_ID:
            print("[DEBUG] Detected user message in forum thread.")
            await post_help_button(message.channel)

    @app_commands.command(name="anon-newsite", description="Submit a new anonymous site review")
    async def anon_newsite(self, interaction: discord.Interaction, site_name: str, stars: int, review: str):
        if not 1 <= stars <= 5:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Star Rating",
                    description="Please enter a star rating between 1 and 5.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        forum = interaction.guild.get_channel(FIELD_FORUM_CHANNEL_ID)
        thread = await forum.create_thread(name=site_name, content=f"{'⭐' * stars} - {review}")
        await post_help_button(thread)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Review Submitted",
                description=f"Your anonymous review for **{site_name}** has been posted.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @app_commands.command(name="anon-addreview", description="Add an anonymous review to an existing site thread")
    @app_commands.describe(thread="The forum thread where you'd like to add a review.")
    async def anon_addreview(self, interaction: discord.Interaction, thread: discord.Thread, stars: int, review: str):
        if not 1 <= stars <= 5:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Star Rating",
                    description="Please enter a star rating between 1 and 5.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        await thread.send(f"{'⭐' * stars} - {review}")
        await post_help_button(thread)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Review Added",
                description=f"Your anonymous review was added to **{thread.name}**.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ReviewCommands(bot))
