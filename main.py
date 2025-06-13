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
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

# Flask keep-alive server
app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Start keep-alive thread
Thread(target=run_flask).start()

# Set up Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Load your commands.py file as a Cog
async def load_extensions():
    await bot.load_extension("commands")  # assumes the file is named commands.py

# ✅ Sync the slash commands when the bot is ready
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# ✅ This is your anon DM fallback (optional)
@bot.command()
async def anon(ctx, *, message: str):
    if ctx.guild is not None:
        await ctx.send("❌ Please send this command in a DM for anonymity.")
        return

    channel = bot.get_channel(CHANNEL_ID)
    log_channel = bot.get_channel(LOG_CHANNEL_ID)

    if channel:
        await channel.send(f"🕵️ **Anonymous Message:**\n{message}")
    if log_channel:
        await log_channel.send(f"📩 Anonymous message from <@{ctx.author.id}>:\n{message}")

    await ctx.send("✅ Your message has been sent anonymously.")

# ✅ Main async runner
async def main():
    await load_extensions()
    await bot.start(TOKEN)

# ✅ Kick off the bot
asyncio.run(main())
