import os
import discord
from discord.ext import commands
from commands import ReviewButtons

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(ReviewButtons(bot))  # Register persistent buttons
    await bot.tree.sync()

async def load_extensions():
    await bot.load_extension("commands")

if __name__ == "__main__":  # ✅ Corrected line
    import asyncio
    asyncio.run(load_extensions())
    bot.run(TOKEN)
