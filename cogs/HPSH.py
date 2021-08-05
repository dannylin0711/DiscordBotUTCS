import discord
import os
import datetime
import time
import sqlite3
import pytz
import random
from datetime import timezone,timedelta
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get
from discord import Guild
from discord import Client
from discord import opus

startuptime = datetime.datetime.now()


class HPSH(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # await bot.get_channel(516470319242805272).send('我來嘍喵~')
    # @commands.command()
    # async def 子暘語錄(self, ctx):
    #     """這是 topax 的語錄 """
    #     f = open("cogs/asset/text/topax.txt",'r',encoding="utf-8")
    #     topax = f.readlines()
    #     totalnum = len(topax)
    #     randomnum = random.randint(0, totalnum-1)
    #     await ctx.send(topax[randomnum])
    
    @commands.command()
    async def 子暘語錄(self, ctx, a: int=-1):
        """這是 topax 的語錄 """
        
        static_guild_id = 406411335778304000
        static_topax_id = 294437986899329025
        if ctx.guild.id == static_guild_id:
            tempguild = self.bot.get_guild(static_guild_id)
            topax_member = await tempguild.fetch_member(static_topax_id)
        
            embed=discord.Embed()
            embed.set_author(name=topax_member.display_name,icon_url=topax_member.avatar_url)
        
            f = open("cogs/asset/text/topax.txt", 'r', encoding="utf-8")
            topax = f.readlines()
            if a == -1:
                totalnum = len(topax)
                randomnum = random.randint(0, totalnum-1)
                embed.add_field(name=topax[randomnum],value="by 周子暘topax",inline=False)
                embed.set_footer(text=("子暘語錄 #"+str(randomnum+1)))
                await ctx.send(embed=embed)
            else:
                embed.add_field(name=topax[a-1],value="by 周子暘topax",inline=False)
                embed.set_footer(text=("子暘語錄 #"+str(a)))
                await ctx.send(embed=embed)
        else:
            await ctx.send("這個伺服器不能使用這個指令喔~")
            
    @commands.command()
    async def 新增子暘語錄(self, ctx, a: str):
        """這是 topax 的語錄 """
        
        static_guild_id = 406411335778304000
        static_topax_id = 294437986899329025
        tempBool = False
        if ctx.guild.id == static_guild_id:
            f = open("cogs/asset/text/topax.txt",'r',encoding="utf-8")
            templist = f.readlines()
            #print(templist)
            f.close()
            for t in templist:
                if str(t) == a+"\n":
                    tempBool = True
            if tempBool:
                await ctx.send("已經有這個語錄了")
            else:
                f = open("cogs/asset/text/topax.txt",'a',encoding="utf-8")
                f.write(a+"\n")
                f.close()
                await ctx.send("已經新增至第"+str(len(templist)+1)+"個語錄了~")
        else:
            await ctx.send("這個伺服器不能使用這個指令喔~")
    
    @commands.command()
    async def 檢視子暘語錄(self, ctx):
        """這是 topax 的語錄 """
        
        static_guild_id = 406411335778304000
        static_topax_id = 294437986899329025
        tempBool = False
        if ctx.guild.id == static_guild_id:
            f = open("cogs/asset/text/topax.txt",'r',encoding="utf-8")
            templist = f.readlines()
            a = '```'
            tempnum = 1;
            for t in templist:
                a += "{:-2d}. {text}".format(tempnum,text=t)
                tempnum += 1
            a += "```"
            await ctx.send(a)
        else:
            await ctx.send("這個伺服器不能使用這個指令喔~")
    
def setup(bot):
    bot.add_cog(HPSH(bot))
