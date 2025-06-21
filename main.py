# main.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from commands import ReviewButtons

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(ReviewButtons(bot))  # Register persistent view
    await bot.tree.sync()

if __name__ == "__main__":
    bot.run(TOKEN)
