import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get


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

@bot.command()
async def 測試(ctx):
    await ctx.send('你到底想幹嘛')

@bot.command()
async def penguinLaugh(ctx):
    emoji = get(bot.get_all_emojis,name='Penguin')
    await ctx.send(emoji)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send('打錯指令辣')
        return
    raise error






bot.run('NjI2NjA1NjQxMDkxNTE0Mzc4.XYwzFg.bKob86Qwh4HkNnCFbutEStOj7VU')