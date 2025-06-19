import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive

# Keep-alive server for Render
keep_alive()

# Define bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")

initial_extensions = ["commands"]

def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            staff_role = discord.utils.get(interaction.guild.roles, name="staff")
            if staff_role in interaction.user.roles:
                return True
            else:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return False
        except AttributeError:
            await interaction.response.send_message("This must be used in a server.", ephemeral=True)
            return False
    return app_commands.check(predicate)

@bot.tree.command(name="load", description="Loads an extension.")
@is_staff()
@app_commands.describe(extension="Extension name")
async def load(interaction: discord.Interaction, extension: str):
    try:
        await bot.load_extension(extension)
        await interaction.response.send_message(f"{extension} loaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error loading extension: {e}", ephemeral=True)

@bot.tree.command(name="unload", description="Unloads an extension.")
@is_staff()
@app_commands.describe(extension="Extension name")
async def unload(interaction: discord.Interaction, extension: str):
    try:
        await bot.unload_extension(extension)
        await interaction.response.send_message(f"{extension} unloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error unloading extension: {e}", ephemeral=True)

@bot.tree.command(name="reload", description="Reloads an extension.")
@is_staff()
@app_commands.describe(extension="Extension name")
async def reload(interaction: discord.Interaction, extension: str):
    try:
        await bot.reload_extension(extension)
        await interaction.response.send_message(f"{extension} reloaded.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error reloading extension: {e}", ephemeral=True)

@bot.tree.command(name="ping", description="Get latency.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Latency: {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="shutdown", description="Shut down the bot.")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down now.", ephemeral=True)
    await bot.close()

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
        print(f"✅ Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    # Add persistent button view
    from commands import ReviewButtons
    bot.add_view(ReviewButtons())

    # Send or update persistent button message
    review_channel = bot.get_channel(1381803347564171286)
    if review_channel:
        async for msg in review_channel.history(limit=50):
            if msg.author == bot.user and "Choose an action" in msg.content:
                await msg.edit(view=ReviewButtons())
                break
        else:
            await review_channel.send("📌 **Choose an action below to submit anonymously:**", view=ReviewButtons())

bot.run(os.environ["DISCORD_TOKEN"])
