import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from commands import ReviewButtons

# Keep-alive for Render
keep_alive()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")

initial_extensions = ["commands"]

# Staff check decorator
def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        staff_role = discord.utils.get(interaction.guild.roles, name="staff")
        if staff_role in interaction.user.roles:
            return True
        await interaction.response.send_message("You do not have permission.", ephemeral=True)
        return False
    return app_commands.check(predicate)

# Management commands
@bot.tree.command(name="load", description="Load an extension.")
@is_staff()
@app_commands.describe(extension="Extension name (e.g., commands)")
async def load(interaction: discord.Interaction, extension: str):
    try:
        await bot.load_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} loaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: ```{e}```", ephemeral=True)

@bot.tree.command(name="reload", description="Reload an extension.")
@is_staff()
@app_commands.describe(extension="Extension name (e.g., commands)")
async def reload(interaction: discord.Interaction, extension: str):
    try:
        await bot.reload_extension(extension.lower())
        await interaction.response.send_message(f"{extension.lower()} reloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: ```{e}```", ephemeral=True)

@bot.tree.command(name="shutdown", description="Shutdown the bot.")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down.", ephemeral=True)
    await bot.close()

@bot.tree.command(name="ping", description="Bot latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)

# On ready
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="you 👀"), status=discord.Status.online)
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    for ext in initial_extensions:
        try:
            await bot.load_extension(ext)
            print(f"✅ Extension loaded: {ext}")
        except Exception as e:
            print(f"❌ Failed to load {ext}: {e}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    # Register persistent view and send button panel if not already there
    bot.add_view(ReviewButtons())
    submit_channel_id = 1381803347564171286
    channel = bot.get_channel(submit_channel_id)
    if channel:
        try:
            async for msg in channel.history(limit=10):
                if any(view for view in msg.components):
                    break
            else:
                await channel.send("Click a button below to submit anonymously:", view=ReviewButtons())
        except Exception as e:
            print(f"❌ Could not send button message: {e}")

# Run the bot
bot.run(os.environ["DISCORD_TOKEN"])
