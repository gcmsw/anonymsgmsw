import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SUBMIT_CHANNEL_ID = int(os.getenv("SUBMIT_CHANNEL_ID", 0))

# Initialize keep-alive Flask server for Render
keep_alive()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True
intents.reactions = True
intents.guild_messages = True
intents.guild_reactions = True

bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")

INITIAL_EXTENSIONS = ["commands"]

# Permission check for staff/admins
def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message("You don’t have permission to use this command.", ephemeral=True)
        return False
    return app_commands.check(predicate)

# Lifecycle: on_ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        for ext in INITIAL_EXTENSIONS:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
    except Exception as e:
        print(f"❌ Failed to load extension: {ext} — {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    # Register persistent views (e.g., buttons)
    from commands import ReviewButtons
    bot.add_view(ReviewButtons())

    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="anonymous reviews"),
        status=discord.Status.online
    )

# Staff-only load/unload/reload commands
@bot.tree.command(name="load", description="Load an extension (admin only)")
@app_commands.describe(extension="Extension name to load (e.g., commands)")
@is_staff()
async def load(interaction: discord.Interaction, extension: str):
    try:
        await bot.load_extension(extension)
        await interaction.response.send_message(f"✅ Loaded `{extension}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error loading `{extension}`:\n```{e}```", ephemeral=True)

@bot.tree.command(name="unload", description="Unload an extension (admin only)")
@app_commands.describe(extension="Extension name to unload (e.g., commands)")
@is_staff()
async def unload(interaction: discord.Interaction, extension: str):
    try:
        await bot.unload_extension(extension)
        await interaction.response.send_message(f"✅ Unloaded `{extension}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error unloading `{extension}`:\n```{e}```", ephemeral=True)

@bot.tree.command(name="reload", description="Reload an extension (admin only)")
@app_commands.describe(extension="Extension name to reload (e.g., commands)")
@is_staff()
async def reload(interaction: discord.Interaction, extension: str):
    try:
        await bot.reload_extension(extension)
        await interaction.response.send_message(f"🔄 Reloaded `{extension}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error reloading `{extension}`:\n```{e}```", ephemeral=True)

# Utility
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000, 1)
    await interaction.response.send_message(f"🏓 Pong! `{latency}ms`", ephemeral=True)

# Shutdown (optional, admin only)
@bot.tree.command(name="shutdown", description="Shut down the bot (admin only)")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("👋 Shutting down the bot...", ephemeral=True)
    await bot.close()

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN environment variable not set.")
    bot.run(DISCORD_TOKEN)
