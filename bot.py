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
    emojiStr = '<:Penguin:623835905999896626>'
    Str = emojiStr+'\n'+emojiStr+emojiStr+'\n'+emojiStr
    await ctx.send(Str)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send('打錯指令辣')
        return
    raise error


from discord.utils import get

@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == bot.user:
        return
    if 'RRRR' in message.content:
        emoji = bot.get_emoji(623835905999896626)
        await message.add_reaction(emoji)
        



bot.run('NjI2NjA1NjQxMDkxNTE0Mzc4.XYwzFg.bKob86Qwh4HkNnCFbutEStOj7VU')