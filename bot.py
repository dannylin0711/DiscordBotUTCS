import discord
import os
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get
from discord import Guild
from discord import Client

client = Client
guild = Guild
bot = commands.Bot(command_prefix="$", description='A bot that greets the user back.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == bot.user:
        return
    if 'RRRR' in message.content:
        emoji = bot.get_emoji(623835905999896626)
        await message.add_reaction(emoji)
    await bot.process_commands(message)

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

    await ctx.send("""<:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626><:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626>""")

@bot.command()
async def emoji(ctx):
    emojiList = bot.emojis
    emojiString = "<:"
    emojiString += (emojiList[1].name + ":"+str(emojiList[1].id))+">"
    await ctx.send(emojiString)
    

@bot.command()
async def nameOfGuild(ctx):
    
    await ctx.send('name')

@bot.command()
async def test(ctx):
    await ctx.send("""This is a test message!
這是測試訊息""")

@bot.command()
async def hahaha(ctx):
    await ctx.send("""HAHAHAHAHAHAHAHAHAHA""")

@bot.command(pass_context=True)
async def join(ctx):
    channel = ctx.message.author.voice.channel
    await bot.join_voice_channel(channel)

@bot.command(pass_context=True)
async def leave(ctx):
    server = ctx.message.server
    voice_client = bot.voice_client_in(server)
    await voice_client.disconnect()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        await ctx.send('打錯指令辣')
        return
    raise error

BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

bot.run(BOT_TOKEN)