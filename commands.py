# commands.py
import discord
from discord.ext import commands
from discord import app_commands

class SimpleModal(discord.ui.Modal, title="Simple Test Modal"):
    test_input = discord.ui.TextInput(label="Say something!")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"You said: {self.test_input.value}", ephemeral=True)

class ReviewButtons(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Open Modal", style=discord.ButtonStyle.primary, custom_id="open_modal")
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SimpleModal())

class PostButtons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="post-buttons")
    async def post_buttons(self, interaction: discord.Interaction):
        view = ReviewButtons(self.bot)
        await interaction.response.send_message("Click to open a modal:", view=view)

async def setup(bot):
    await bot.add_cog(PostButtons(bot))
