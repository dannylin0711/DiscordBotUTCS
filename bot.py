import datetime
import os

from discord import Client
from discord import Guild
from discord.ext import commands


client = Client
guild = Guild
bot = commands.Bot(command_prefix="$", description='一隻艾路貓，會狠狠的戳人。')



# discord.opus.load_opus('libopus.dylib')


@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    await ctx.send("已載入插件"+extension)


@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send("已卸下插件"+extension)

@bot.command()
async def reload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.send("已重新載入插件"+extension)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

BOT_TOKEN = is_prod = os.environ.get('TOKEN', None)
bot.run(BOT_TOKEN)
