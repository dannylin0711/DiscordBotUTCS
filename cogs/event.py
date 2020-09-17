import discord
import os
import datetime
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get
from discord import Guild
from discord import Client
from discord import opus


class Events(commands.Cog):
    @commands.Cog.listener()
    async def on_message(self,message):
    # we do not want the bot to reply to itself
        if message.author == self.bot.user:
            return
        if 'RRRR' in message.content:
            emoji = self.bot.get_emoji(623835905999896626)
            await message.add_reaction(emoji)
            
        temp = message.content.replace(" ","")
        if 'ㄎㄧㄤ' in temp:
            emoji = self.bot.get_emoji(699474147818078358)
            await message.add_reaction(emoji)
        
        
    @commands.Cog.listener()
    async def on_ready(self):
        print('Logged in as')
        print(self.bot.user.name)
        print(self.bot.user.id)
        print('------')
        activity = discord.Streaming(name='當一隻艾路貓',url='https://www.twitch.tv/dannylin0711')
        activity.game = "Monster Hunter World"
        await self.bot.change_presence(status=discord.Status.idle,activity=activity)
        
    @commands.Cog.listener()
    async def on_command_error(self,ctx, error):
        print(error)
        if isinstance(error, CommandNotFound):
            await ctx.send('打錯指令辣')
            return
        raise error
    
    def __init__(self,bot):
        self.bot = bot
        
def setup(bot):
    bot.add_cog(Events(bot))