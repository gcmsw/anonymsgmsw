import os
import asyncio
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))  # Optional: for fast testing in one server

intents = discord.Intents.default()
intents.members = True  # Enable privileged intent if needed

bot = commands.Bot(command_prefix="!", intents=intents)

# Optional: force sync to a dev/test server for faster updates
@bot.event
async def on_ready():
    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            await bot.tree.sync(guild=guild)
            print(f"Synced commands to guild {GUILD_ID}")
        else:
            await bot.tree.sync()
            print("Synced global commands")
        print(f"Logged in as {bot.user}")
    except Exception as e:
        print("Error syncing commands:", e)

# Load the commands cog
async def load_extensions():
    try:
        await bot.load_extension("commands")
        print("Loaded commands cog")
    except Exception as e:
        print("Error loading cog:", e)

# Flask keep-alive (Render)
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

async def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    async with bot:
        await load_extensions()
        if not TOKEN:
            print("❌ DISCORD_TOKEN is missing!")
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("Startup error:", e)
