import os
import discord
from discord.ext import commands
from keep_alive import keep_alive
from commands import ReviewButtons

# Start Flask server for Render uptime
keep_alive()

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

# Define bot
bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")  # Optional

# Load command extension on startup
INITIAL_EXTENSIONS = ["commands"]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    for ext in INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")

    # Register persistent view so buttons stay after restart
    bot.add_view(ReviewButtons())

# Run the bot
bot.run(os.environ["DISCORD_TOKEN"])
