import os
import discord
from discord.ext import commands
from discord import app_commands
from keep_alive import keep_alive
from commands import HelpButtonView

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
    bot.add_view(ReviewButtons())
    print("✅ Registered persistent ReviewButtons view")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_message(message: discord.Message):
    try:
        if message.author.bot:
            return  # Ignore bot messages from other bots

        forum_channel_id = int(os.getenv("FORUM_CHANNEL_ID"))
        if not isinstance(message.channel, discord.Thread):
            return
        if message.channel.parent_id != forum_channel_id:
            return

        thread = message.channel

        # Delete old help button messages from the bot
        async for msg in thread.history(limit=50):
            if msg.author == bot.user and msg.components:
                if msg.components[0].children[0].custom_id == "thread_help_button":
                    await msg.delete()

        # Post new help button
        await thread.send(
            "Use the slash commands below to anonymously add reviews, questions, or replies in this thread.",
            view=HelpButtonView()
        )

    except Exception as e:
        print(f"❌ Error posting help button in thread: {e}")
