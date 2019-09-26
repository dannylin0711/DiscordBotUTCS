import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="$", description='A bot that greets the user back.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def add(ctx, a: int, b: int):
    await ctx.send(a+b)

@bot.command()
async def laugh(ctx):
    await ctx.send('哈哈...')


bot.run('NjI2NjA1NjQxMDkxNTE0Mzc4.XYwzFg.bKob86Qwh4HkNnCFbutEStOj7VU')