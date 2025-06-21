import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from commands import ReviewButtons  # Ensure this is correct

# Start keep-alive Flask server (for Render)
keep_alive()

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")

initial_extensions = ["commands"]  # Extension module(s) to load

# Staff permission check decorator
def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            staff_role = discord.utils.get(interaction.guild.roles, name="staff")
            if staff_role in interaction.user.roles:
                return True
            else:
                await interaction.response.send_message("You don’t have permission to use this.", ephemeral=True)
                return False
        except AttributeError:
            await interaction.response.send_message("Something went wrong. Make sure you're in the server and have the right role.", ephemeral=True)
            return False
    return app_commands.check(predicate)

# Admin commands
@bot.tree.command(name="load", description="Loads an extension.")
@app_commands.describe(extension="Currently available: commands")
@is_staff()
async def load(interaction: discord.Interaction, extension: str):
    try:
        await bot.load_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} loaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```{type(e).__name__}: {e}```", ephemeral=True)

@bot.tree.command(name="unload", description="Unloads an extension.")
@app_commands.describe(extension="Currently available: commands")
@is_staff()
async def unload(interaction: discord.Interaction, extension: str):
    try:
        await bot.unload_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} unloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```{type(e).__name__}: {e}```", ephemeral=True)

@bot.tree.command(name="reload", description="Reloads an extension.")
@app_commands.describe(extension="Currently available: commands")
@is_staff()
async def reload(interaction: discord.Interaction, extension: str):
    try:
        await bot.reload_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} reloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```{type(e).__name__}: {e}```", ephemeral=True)

@bot.tree.command(name="ping", description="Shows bot latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Latency: {round(bot.latency * 1000, 1)}ms", ephemeral=True)

@bot.tree.command(name="shutdown", description="Shuts the bot down.")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down now.", ephemeral=True)
    await bot.close()

# Run setup on bot ready
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="you"),
        status=discord.Status.do_not_disturb
    )
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Loaded extension: {ext}")
        except Exception as e:
            print(f"❌ Failed to load extension {ext}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    # 🧠 Register persistent view for buttons
    bot.add_view(ReviewButtons(bot))

# Run the bot
bot.run(os.environ["DISCORD_TOKEN"])
