import discord
from discord.ext import commands

bot = commands.Bot(commands_prefix='$')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def add(ctx, a: int, b: int):
    await ctx.send(a+b)

bot.run('NjI2NjA1NjQxMDkxNTE0Mzc4.XYwnOg.LgSd8EwhAFIq1Pyr35eeH7K18mk')