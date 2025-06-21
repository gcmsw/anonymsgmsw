import os
import discord
from discord.ext import commands
from keep_alive import keep_alive

# Keep-alive server for Render
keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)

initial_extensions = ["commands"]

@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="your confessions 👀"),
        status=discord.Status.online
    )

    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")

    # Register persistent button view
    try:
        from commands import ReviewButtons
        bot.add_view(ReviewButtons(bot))
        print("✅ Registered persistent ReviewButtons view")
    except Exception as e:
        print(f"❌ Failed to register buttons view: {e}")

    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

bot.run(os.environ["DISCORD_TOKEN"])
