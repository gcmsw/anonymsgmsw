import discord
from discord.ext import commands

class DebugCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            print("[DEBUG] on_message fired")
            print(f"[DEBUG] Author: {message.author} | Bot? {message.author.bot}")
            print(f"[DEBUG] Channel: {message.channel}")

            if message.author.bot:
                print("[DEBUG] Ignored bot message")
                return

            if isinstance(message.channel, discord.Thread):
                parent = message.channel.parent
                print(f"[DEBUG] Parent channel: {parent} | Type: {type(parent)}")
                if isinstance(parent, discord.ForumChannel):
                    print("[DEBUG] Thread is inside a forum")
                    if parent.id == 1384999875237646508:
                        print("[DEBUG] Matched target forum channel ID")
                        await message.channel.send("[DEBUG] This is a test response from on_message listener")
        except Exception as e:
            print(f"[ERROR] on_message failed: {e}")

async def setup(bot):
    await bot.add_cog(DebugCog(bot))
