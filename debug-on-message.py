import discord
from discord.ext import commands

class DebugCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        print("on_message fired")
        print(f"Author: {message.author}")
        print(f"Channel: {message.channel}")

        if message.author.bot:
            print("Ignored bot message")
            return

        if isinstance(message.channel, discord.Thread):
            parent = message.channel.parent
            print(f"Parent: {parent}")
            if isinstance(parent, discord.ForumChannel):
                print("In a forum channel")
                if parent.id == 1384999875237646508:
                    print("Correct forum ID matched. Should trigger help button logic here.")

async def setup(bot):
    await bot.add_cog(DebugCog(bot))
