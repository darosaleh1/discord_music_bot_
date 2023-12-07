import discord
from discord.ext import commands
import os, asyncio

from help_cog import help_cog
from music_cog import music_cog

# if not discord.opus.is_loaded():
#     # Attempt to load Opus; replace 'opus' with the path to the Opus library if necessary
#     discord.opus.load_opus('opus')


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

bot.remove_command("help")


async def main():
    async with bot:
        await bot.add_cog(help_cog(bot))
        await bot.add_cog(music_cog(bot))
        await bot.start('MTE4MTczNjUyNzQ2MjY2NjQyMA.GrbDp1.wicTjh-zvfF1HydoI56wH4BeJg4rTwyIUs_Nbk')

asyncio.run(main())
