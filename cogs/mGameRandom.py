import discord
import os
import datetime
import time
import sqlite3
import pytz
import random
import json
from datetime import timezone,timedelta
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get
from discord import Guild,Colour
from discord import Client
from discord import opus
from colorthief import ColorThief

class mGameRandom(commands.Cog):

    def __init__(self, bot:commands.Bot):
        self.bot:commands.Bot = bot
        self.maiData = json.load(open('cogs/asset/text/maimai.json',encoding="utf-8"))
        
        
    @commands.command()
    async def 我想打mai(self, ctx:commands.Context, a: int=-1):
        if a == -1:
            # print(self.maiData)
            temp = random.randint(0,len(self.maiData)-1)
            randData = self.maiData[temp]
            color_thief = ColorThief(randData['assetPath'])
            # get the dominant color
            dominant_color = color_thief.get_color(quality=1)
            # print(dominant_color)
            title = randData['name']
            if randData['type'] == 'DX':
                title += ' (DX 譜面)'
            embed=discord.Embed(title=title,description=randData["artist"],color=Colour.from_rgb(dominant_color[0],dominant_color[1],dominant_color[2]))
            file = discord.File(randData['assetPath'],filename='jacket.png')
             
            embed.set_thumbnail(url='attachment://jacket.png')
            embed.add_field(name='Basic', value=randData['difficulty']['Basic'], inline=True)
            embed.add_field(name='Advanced', value=randData['difficulty']['Advanced'], inline=False)
            embed.add_field(name='Expert', value=randData['difficulty']['Expert'], inline=False)
            embed.add_field(name='Master', value=randData['difficulty']['Master'], inline=False)
            # print(randData['difficulty']['Re:Master'])
            if not ('0+' == randData['difficulty']['Re:Master'] or '0+' == randData['difficulty']['Re:Master']):
                embed.add_field(name='Re:Master', value=randData['difficulty']['Re:Master'], inline=False)
            # await ctx.send(self.maiData[temp])
            await ctx.send('為您挑選出：',file=file,embed=embed)
            
async def setup(bot):
    await bot.add_cog(mGameRandom(bot))
