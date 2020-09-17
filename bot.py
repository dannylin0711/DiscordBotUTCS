import discord
import os
import datetime
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get
from discord import Guild
from discord import Client

client = Client
guild = Guild
bot = commands.Bot(command_prefix="$", description='一隻艾路貓，會狠狠的戳人。')
startuptime = datetime.datetime.now()
#discord.opus.load_opus('libopus.dylib')



@bot.command()
async def load(ctx, extension):
    bot.load_extension(f'cogs.{extension}')
    
@bot.command()
async def unload(ctx, extension):
    bot.unload_extension(f'cogs.{extension}')
    
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')


BOT_TOKEN = 'NjI2NjA1NjQxMDkxNTE0Mzc4.XbP6Qg.oAQ93md_USdkF3dDNNDbx-A0RCE'
bot.run(BOT_TOKEN)