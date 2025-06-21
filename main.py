import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from commands import ReviewButtons  # ✅ Needed to register the button panel

# 🌱 Keep-alive server for Render
keep_alive()

# 🌟 Define bot
bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
bot.remove_command("help")

initial_extensions = ["commands"]

# ✅ Staff permission check
def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            staff_role = discord.utils.get(interaction.guild.roles, name="staff")
            if staff_role in interaction.user.roles:
                return True
            else:
                await interaction.response.send_message(
                    "You do not have permission to use this command.", ephemeral=True
                )
                return False
        except AttributeError:
            await interaction.response.send_message(
                "Something went wrong. Please ensure you're using this in a server and have the required permissions.",
                ephemeral=True
            )
            return False
    return app_commands.check(predicate)

# 🧩 Management commands
@bot.tree.command(name="load", description="Loads the chosen extension.")
@app_commands.describe(extension="Current extensions: commands")
@is_staff()
async def load(interaction: discord.Interaction, extension: str):
    try:
        await bot.load_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} loaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```py\n{type(e).__name__}: {str(e)}\n```", ephemeral=True)

@bot.tree.command(name="unload", description="Unloads the chosen extension.")
@app_commands.describe(extension="Current extensions: commands")
@is_staff()
async def unload(interaction: discord.Interaction, extension: str):
    try:
        await bot.unload_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} unloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```py\n{type(e).__name__}: {str(e)}\n```", ephemeral=True)

@bot.tree.command(name="reload", description="Reloads the chosen extension.")
@app_commands.describe(extension="Current extensions: commands")
@is_staff()
async def reload(interaction: discord.Interaction, extension: str):
    try:
        await bot.reload_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} reloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"```py\n{type(e).__name__}: {str(e)}\n```", ephemeral=True)

@bot.tree.command(name="ping", description="Get the bot's current latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Latency: {round(bot.latency * 1000, 1)}ms", ephemeral=True)

@bot.tree.command(name="shutdown", description="Shuts the bot down.")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down now.")
    await bot.close()

# ✅ On ready
@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="you"),
        status=discord.Status.do_not_disturb
    )
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"✅ Loaded extension: {extension}")
        except Exception as e:
            print(f"❌ Failed to load extension {extension}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    # ✅ Register the persistent button panel
    bot.add_view(ReviewButtons())

# 🟢 Run bot
bot.run(os.environ["DISCORD_TOKEN"])
