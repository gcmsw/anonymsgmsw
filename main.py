import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive

# Keep-alive server for Render
keep_alive()

# Define bot
bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
bot.remove_command("help")  # Optional: remove default help

initial_extensions = ["commands"]  # Extension file(s)

# Staff permission check
def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            staff_role = discord.utils.get(interaction.guild.roles, name="staff")
            if staff_role in interaction.user.roles:
                return True
            else:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return False
        except AttributeError:
            await interaction.response.send_message("Something went wrong. Please ensure you're using this in a server and have the required permissions.", ephemeral=True)
            return False
    return app_commands.check(predicate)

# Management commands
@bot.tree.command(name="load", description="Loads the chosen extension.")
@app_commands.describe(extension="Current extensions: commands")
@is_staff()
async def load(interaction: discord.Interaction, extension: str):
    try:
        await bot.load_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} loaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```py\n{type(e).__name__}: {str(e)}\n```", ephemeral=True)

@bot.tree.command(name="unload", description="Unloads the chosen extension.")
@app_commands.describe(extension="Current extensions: commands")
@is_staff()
async def unload(interaction: discord.Interaction, extension: str):
    try:
        awai
