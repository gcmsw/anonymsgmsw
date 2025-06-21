import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from commands import ReviewButtons  # Make sure this import works with your structure

# Keep-alive for Render
keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="?", intents=intents)
bot.remove_command("help")

# Load extension(s)
initial_extensions = ["commands"]

# Staff check decorator
def is_staff():
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            staff_role = discord.utils.get(interaction.guild.roles, name="staff")
            if staff_role in interaction.user.roles:
                return True
            else:
                await interaction.response.send_message("You do not have permission.", ephemeral=True)
                return False
        except AttributeError:
            await interaction.response.send_message("This only works in a server.", ephemeral=True)
            return False
    return app_commands.check(predicate)

# Admin-only command to post the button panel
@bot.tree.command(name="post-buttons", description="Post the anonymous review buttons")
@is_staff()
async def post_buttons(interaction: discord.Interaction):
    channel_id = int(os.getenv("SUBMIT_CHANNEL_ID"))
    channel = bot.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("Could not find the submit-site-review channel.", ephemeral=True)
        return
    await channel.send("Submit an anonymous message using one of the buttons below:", view=ReviewButtons(bot))
    await interaction.response.send_message("Posted the button panel!", ephemeral=True)

# Ping and shutdown
@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! `{round(bot.latency * 1000)}ms`", ephemeral=True)

@bot.tree.command(name="shutdown", description="Shuts the bot down.")
@is_staff()
async def shutdown(interaction: discord.Interaction):
    await interaction.response.send_message("Shutting down...", ephemeral=True)
    await bot.close()

# Bot ready
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
        await bot.tree.sync()
        print("✅ Synced slash commands.")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    # ✅ Register persistent view
    bot.add_view(ReviewButtons(bot))

# Run the bot
bot.run(os.environ["DISCORD_TOKEN"])
