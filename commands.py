import os
import discord
from discord import app_commands
from discord.ext import commands

FIELD_FORUM_CHANNEL_ID = int(os.getenv("FIELD_FORUM_CHANNEL_ID"))
SUBMIT_REVIEW_CHANNEL_ID = int(os.getenv("SUBMIT_REVIEW_CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

class SubmitType:
    NEWSITE = "anon-newsite"
    ADDREVIEW = "anon-addreview"
    QUESTION = "anon-question"
    REPLY = "anon-reply"

class SubmitModal(discord.ui.Modal):
    def __init__(self, command_type):
        super().__init__(title="Submit Anonymous Message")
        self.command_type = command_type
        self.site_name = discord.ui.TextInput(label="Site Name", required=True)
        self.content = discord.ui.TextInput(label="Your Message", style=discord.TextStyle.paragraph, required=True)
        self.stars = discord.ui.TextInput(label="Star Rating (1–5)", required=False)

        self.add_item(self.site_name)
        if command_type in [SubmitType.ADDREVIEW, SubmitType.NEWSITE]:
            self.add_item(self.stars)
        self.add_item(self.content)

    async def on_submit(self, interaction: discord.Interaction):
        # Star validation
        if self.command_type in [SubmitType.ADDREVIEW, SubmitType.NEWSITE]:
            if self.stars.value:
                try:
                    rating = int(self.stars.value)
                    if rating < 1 or rating > 5:
                        raise ValueError
                except ValueError:
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            title="❌ Invalid Star Rating",
                            description="Star rating must be a number between 1 and 5.",
                            color=discord.Color.red(),
                        ),
                        ephemeral=True
                    )
                    return

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Submitted!",
                description="Your anonymous message has been posted.",
                color=discord.Color.green(),
            ),
            ephemeral=True
        )

class ReviewButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Submit New Site Review", style=discord.ButtonStyle.primary, custom_id="submit_new_review"))

class HelpButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="How to Post Anonymously", style=discord.ButtonStyle.secondary, url="https://yourlink.here"))

class AnonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ReviewButtons())
        print(f"Bot is ready. Logged in as {self.bot.user}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        if isinstance(message.channel, discord.Thread) and message.channel.parent_id == FIELD_FORUM_CHANNEL_ID:
            existing = [m async for m in message.channel.history(limit=10) if m.author.bot and any(
                b.label == "How to Post Anonymously" for b in getattr(m.components[0], 'children', [])
            )] if message.channel else []
            for m in existing:
                await m.delete()
            await message.channel.send(embed=discord.Embed(
                title="🛡️ Post Anonymously",
                description="Use `/anon-addreview`, `/anon-question`, or `/anon-reply` to post without showing your name.",
                color=discord.Color.blue()
            ), view=HelpButtonView())

async def setup(bot):
    await bot.add_cog(AnonCog(bot))
