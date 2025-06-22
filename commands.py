import discord
from discord.ext import commands
from discord import app_commands
import os

SUBMIT_CHANNEL_ID = int(os.environ["SUBMIT_CHANNEL_ID"])
FORUM_CHANNEL_ID = int(os.environ["FORUM_CHANNEL_ID"])
LOG_CHANNEL_ID = int(os.environ["LOG_CHANNEL_ID"])
GUILD_ID = int(os.environ["GUILD_ID"])

class SubmitModal(discord.ui.Modal, title="Submit New Site Review"):
    site_name = discord.ui.TextInput(label="Site Name", placeholder="Name of the field site")
    review = discord.ui.TextInput(label="Your Review", style=discord.TextStyle.paragraph, placeholder="Enter your anonymous review here", required=True)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        forum = interaction.guild.get_channel(FORUM_CHANNEL_ID)
        site_name = self.site_name.value.strip()
        review = self.review.value.strip()

        existing_thread = discord.utils.find(lambda t: site_name.lower() in t.name.lower(), forum.threads)
        if existing_thread:
            await existing_thread.send(f"""📌 Anonymous Review:\n{review}""")
            await interaction.response.send_message(f"✅ Review posted to existing thread: {existing_thread.mention}", ephemeral=True)
        else:
            new_thread = await forum.create_thread(name=site_name, content=f"📌 Anonymous Review:\n{review}")
            await interaction.response.send_message(f"✅ New site thread created: {new_thread.mention}", ephemeral=True)
            await post_help_button(new_thread, self.bot)

class ReviewButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Submit New Site Review", style=discord.ButtonStyle.primary, custom_id="submit_review")
    async def submit_review(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SubmitModal(self.bot))

async def post_help_button(thread: discord.Thread, bot):
    async for msg in thread.history(limit=50):
        if msg.author == bot.user and msg.components:
            await msg.delete()

    view = HelpButtonView()
    embed = discord.Embed(title="Need Help Posting Anonymously?", description="Use the slash commands below directly in this thread:", color=discord.Color.orange())
    embed.add_field(name="/anon-addreview", value="Add another review about this site", inline=False)
    embed.add_field(name="/anon-question", value="Ask a question anonymously", inline=False)
    embed.add_field(name="/anon-reply", value="Reply anonymously to a message above", inline=False)
    await thread.send(embed=embed, view=view)

class HelpButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="How to Post Anonymously", style=discord.ButtonStyle.secondary, custom_id="help_button")
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use the slash commands in this thread: /anon-addreview, /anon-question, /anon-reply", ephemeral=True)

class AnonBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons", description="Post the persistent Submit Review button")
    @app_commands.checks.has_role("Admin")
    async def post_buttons(self, interaction: discord.Interaction):
        view = ReviewButtons(self.bot)
        await interaction.response.send_message("Submit a new site review anonymously:", view=view, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != FORUM_CHANNEL_ID:
            return
        if message.type == discord.MessageType.default and not message.author.bot:
            thread = message.channel if isinstance(message.channel, discord.Thread) else None
            if thread:
                await post_help_button(thread, self.bot)

async def setup(bot):
    await bot.add_cog(AnonBot(bot))
