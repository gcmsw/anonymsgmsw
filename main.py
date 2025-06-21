import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from commands import ReviewButtons  # Ensure this matches the actual file name if renamed

# Keep-alive for Render
keep_alive()

# Intents and bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")

# Load your extensions
initial_extensions = ["commands"]

# Permission check for staff
def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            staff_role = discord.utils.get(interaction.guild.roles, name="staff")
            if staff_role in interaction.user.roles:
                return True
            await interaction.response.send_message("You do not have permission.", ephemeral=True)
            return False
        except AttributeError:
            await interaction.response.send_message("Error: Server-only command.", ephemeral=True)
            return False
    return app_commands.check(predicate)

# Management commands
@bot.tree.command(name="load", description="Loads an extension")
@app_commands.describe(extension="Extension name (e.g. commands)")
@is_staff()
async def load(interaction: discord.Interaction, extension: str):
    try:
        await bot.load_extension(extension)
        await interaction.response.send_message(f"✅ Loaded `{extension}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ {type(e).__name__}: {str(e)}", ephemeral=True)

@bot.tree.command(name="unload", description="Unloads an extension")
@app_commands.describe(extension="Extension name (e.g. commands)")
@is_staff()
async def unload(interaction: discord.Interaction, extension: str):
    try:
        await bot.unload_extension(extension)
        await interaction.response.send_message(f"✅ Unloaded `{extension}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ {type(e).__name__}: {str(e)}", ephemeral=True)

@bot.tree.command(name="reload", description="Reloads an extension")
@app_commands.describe(extension="Extension name (e.g. commands)")
@is_staff()
async def reload(interaction: discord.Interaction, extension: str):
    try:
        await bot.reload_extension(extension)
        await interaction.response.send_message(f"✅ Reloaded `{extension}`", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ {type(e).__name__}: {str(e)}", ephemeral=True)

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="shutdown", description="Shuts the bot down")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down now.", ephemeral=True)
    await bot.close()

# Slash command to post buttons manually
@bot.tree.command(name="post-buttons", description="Post the anonymous message button panel")
@is_staff()
async def post_buttons(interaction: discord.Interaction):
    channel_id = int(os.environ.get("SUBMIT_CHANNEL_ID"))
    channel = bot.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("❌ Could not find the submit channel.", ephemeral=True)
        return
    await channel.send("Click a button below to submit anonymously:", view=ReviewButtons())
    await interaction.response.send_message("✅ Button panel posted.", ephemeral=True)

# Ready event
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="anonymous reviews"),
        status=discord.Status.online
    )
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load {ext}: {e}")

    try:
        bot.add_view(ReviewButtons())  # Persistent view registration
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

# Run the bot
bot.run(os.environ["DISCORD_TOKEN"])
