### main.py

import os
import discord
from discord.ext import commands
from keep_alive import keep_alive
from commands import ReviewButtons

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

EXTENSIONS = ["commands"]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

    # Load extensions
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(ext)
            print(f"Loaded extension: {ext}")
        except Exception as e:
            print(f"Failed to load extension {ext}: {e}")

    # Register persistent views
    bot.add_view(ReviewButtons(bot))

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
