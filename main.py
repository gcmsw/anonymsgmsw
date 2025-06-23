import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

# Flask keep-alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# Load extensions
initial_extensions = ['commands']

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)
    keep_alive()
    bot.run(TOKEN)  # Starts the bot
