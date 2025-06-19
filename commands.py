import discord
from discord import app_commands
from discord.ext import commands

SUBMIT_CHANNEL_ID = 123456789012345678  # replace with your ForumChannel ID

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_thread_autocomplete(self, interaction: discord.Interaction, current: str):
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        if not isinstance(channel, discord.ForumChannel):
            return []

        threads = channel.threads
        return [
            app_commands.Choice(name=thread.name[:100], value=str(thread.id))
            for thread in threads if current.lower() in thread.name.lower()
        ][:25]

    @app_commands.command(name="anon-site", description="Post an anonymous field site review")
    @app_commands.describe(title="Title of your post", content="Your anonymous review content")
    async def anon_site(self, interaction: discord.Interaction, title: str, content: str):
        channel = self.bot.get_channel(SUBMIT_CHANNEL_ID)
        thread = await channel.create_thread(name=title, content=content)
        await interaction.response.send_message("✅ Review posted anonymously!", ephemeral=True)

    @app_commands.command(name="anon-addreview", description="Add an anonymous review to an existing thread")
    @app_commands.describe(thread="Which thread?", content="Your review")
    @app_commands.autocomplete(thread=get_thread_autocomplete)
    async def anon_addreview(self, interaction: discord.Interaction, thread: str, content: str):
        target_thread = await interaction.guild.fetch_channel(int(thread))
        await target_thread.send(content)
        await interaction.response.send_message("✅ Review added anonymously!", ephemeral=True)

    @app_commands.command(name="anon-question", description="Ask a question anonymously in a thread")
    @app_commands.describe(thread="Which thread?", content="Your question")
    @app_commands.autocomplete(thread=get_thread_autocomplete)
    async def anon_question(self, interaction: discord.Interaction, thread: str, content: str):
        target_thread = await interaction.guild.fetch_channel(int(thread))
        await target_thread.send(f"💬 **Question:** {content}")
        await interaction.response.send_message("✅ Question posted anonymously!", ephemeral=True)

    @app_commands.command(name="anon-reply", description="Post an anonymous reply in a thread")
    @app_commands.describe(thread="Which thread?", content="Your reply")
    @app_commands.autocomplete(thread=get_thread_autocomplete)
    async def anon_reply(self, interaction: discord.Interaction, thread: str, content: str):
        target_thread = await interaction.guild.fetch_channel(int(thread))
        await target_thread.send(f"📝 **Reply:** {content}")
        await interaction.response.send_message("✅ Reply posted anonymously!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(CommandsCog(bot))
