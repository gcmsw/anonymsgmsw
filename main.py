import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
import asyncio

keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

initial_extensions = ["commands"]

def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            staff_role = discord.utils.get(interaction.guild.roles, name="Admin")
            return staff_role in interaction.user.roles
        except:
            return False
    return app_commands.check(predicate)

@bot.tree.command(name="ping", description="Check latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! Latency: {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="shutdown", description="Shuts down the bot")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down...", ephemeral=True)
    await bot.close()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your confessions 🙀"))

    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")

    from commands import ReviewButtons
    bot.add_view(ReviewButtons(bot))
    print("✅ Registered persistent ReviewButtons view")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    # Auto-post persistent button if not already there
    submit_channel = bot.get_channel(int(os.environ["SUBMIT_CHANNEL_ID"]))
    if submit_channel:
        async for message in submit_channel.history(limit=10):
            if message.author == bot.user and message.components:
                print("ℹ️ Submit button already present.")
                break
        else:
            await submit_channel.send(
                "📝 Click the button below to submit a new site review:",
                view=ReviewButtons(bot)
            )
            print("✅ Posted submit review button.")
    else:
        print("❌ Could not find submit channel.")


async def main():
    async with bot:
        await bot.start(os.environ["DISCORD_TOKEN"])

asyncio.run(main())
