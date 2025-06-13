from flask import Flask
from threading import Thread
from discord.ext import commands
import discord
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Flask keep-alive server
app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Start keep-alive thread
Thread(target=run_flask).start()

# Set up Discord bot with necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load commands.py as a cog
async def load_extensions():
    await bot.load_extension("commands")  # this must match the filename (commands.py)

# Sync slash commands on ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# Main async entrypoint
async def main():
    await load_extensions()
    await bot.start(TOKEN)

# Start the bot
asyncio.run(main())
