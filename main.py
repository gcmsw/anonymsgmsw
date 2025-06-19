import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive

# Start Flask keep-alive server
keep_alive()

# Define bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="?", intents=intents)

# List of cogs/extensions to load
initial_extensions = ["commands"]

# Staff permission check
def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            staff_role = discord.utils.get(interaction.guild.roles, name="Admin")
            if staff_role in interaction.user.roles:
                return True
            else:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return False
        except AttributeError:
            await interaction.response.send_message("Something went wrong. Please ensure you're in a server with proper roles.", ephemeral=True)
            return False
    return app_commands.check(predicate)

# Admin slash commands
@bot.tree.command(name="load", description="Loads the chosen extension.")
@app_commands.describe(extension="Extension to load (e.g. commands)")
@is_staff()
async def load(interaction: discord.Interaction, extension: str):
    try:
        await bot.load_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} loaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```py\n{type(e).__name__}: {str(e)}\n```", ephemeral=True)

@bot.tree.command(name="unload", description="Unloads the chosen extension.")
@app_commands.describe(extension="Extension to unload (e.g. commands)")
@is_staff()
async def unload(interaction: discord.Interaction, extension: str):
    try:
        await bot.unload_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} unloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```py\n{type(e).__name__}: {str(e)}\n```", ephemeral=True)

@bot.tree.command(name="reload", description="Reloads the chosen extension.")
@app_commands.describe(extension="Extension to reload (e.g. commands)")
@is_staff()
async def reload(interaction: discord.Interaction, extension: str):
    try:
        await bot.reload_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} reloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```py\n{type(e).__name__}: {str(e)}\n```", ephemeral=True)

@bot.tree.command(name="ping", description="Check latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! Latency: {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="shutdown", description="Shuts down the bot")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down...", ephemeral=True)
    await bot.close()

# On ready
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="your confessions 👀"),
        status=discord.Status.online
    )

    # Load extensions
    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")

    # Register persistent button view
    from commands import ReviewButtons
    bot.add_view(ReviewButtons())

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# Run bot
bot.run(os.environ["DISCORD_TOKEN"])
