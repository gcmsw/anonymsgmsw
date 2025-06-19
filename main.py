import discord
from discord.ext import commands
from flask import Flask
import threading
import os
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load extension
@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

async def main():
    async with bot:
        await bot.load_extension("commands")
        await bot.start(os.getenv("DISCORD_TOKEN"))

# Flask keep-alive
app = Flask("")

@app.route("/")
def home():
    return "I'm alive"

def run():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run).start()

# Run bot
asyncio.run(main())
