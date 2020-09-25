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
    
    @commands.Cog.listener()
    async def on_message_delete(self,message):
        if not message.author.bot:
        #    print("\n已刪除的訊息:")
        #    print("　伺服器　　:"+ message.channel.guild.name)
        #    print("　頻道　　　:"+ message.channel.name)
        #    print("　訊息發出者:"+ message.author.display_name)
        #    print("　時間　　　:"+ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        #    print("　訊息內容　:"+message.content+"\n")

            tmessage =  "\n已刪除的訊息:\n"
            tmessage += "　伺服器　　:"+ message.channel.guild.name +"\n"
            tmessage += "　頻道　　　:"+ message.channel.name + "\n"
            tmessage += "　訊息發出者:"+ message.author.display_name + "\n"
            tmessage += "　時間　　　:"+ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
            tmessage += "　訊息內容　:"+ message.content
            me = self.bot.get_user(201293557544255488)    
            await me.send(str(tmessage))

            if message.attachments:
                for a in message.attachments:
                    await me.send(a.url)
        
    @commands.Cog.listener()
    async def on_message_edit(self,before, after):
        if not before.author.bot:
            # print("\n已修改的訊息:")
            # print("　伺服器　　:"+ before.channel.guild.name)
            # print("　頻道　　　:"+ before.channel.name)
            # print("　訊息發出者:"+ before.author.display_name)
            # print("　時間　　　:"+ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # print("　修改前內容:"+ before.content)
            # print("　修改後內容:"+ after.content+"\n")

            tmessage =  "\n已修改的訊息:\n"
            tmessage += "　伺服器　　:"+ before.channel.guild.name +"\n"
            tmessage += "　頻道　　　:"+ before.channel.name + "\n"
            tmessage += "　訊息發出者:"+ before.author.display_name + "\n"
            tmessage += "　時間　　　:"+ datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
            tmessage += "　原訊息內容　:"+ before.content + "\n"
            tmessage += "　修改後內容:"+ after.content
        
            me = self.bot.get_user(201293557544255488)    
            await me.send(str(tmessage))
    
    def __init__(self,bot):
        self.bot = bot
        
def setup(bot):
    bot.add_cog(Events(bot))