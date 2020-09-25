import discord
import os
import datetime
import time
import sqlite3
from pytz import timezone
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get
from discord import Guild
from discord import Client
from discord import opus

startuptime = datetime.datetime.now()


class mainCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dbconnect = sqlite3.connect('petcat.db')
        self.dbcursor = self.dbconnect.cursor()
        print('已載入好感度資料庫')

    # await bot.get_channel(516470319242805272).send('我來嘍喵~')
    @commands.command()
    async def add(self, ctx, a: int, b: int):
        """加法 兩個數字相加 用法: $add a b
        輸出a+b"""
        await ctx.send(a + b)

    @commands.command()
    async def say(self, ctx, a: str):
        """讓機器人說話 因為是艾路貓所以會在尾巴說喵"""
        print("輸入:" + a)
        await ctx.message.delete()
        message = a
        if 'http' not in a:
            if '<:' not in a:
                message += "喵"
        if '主人' in a:
            message = "你才不是主人呢"
        if '啥小' in a or '幹' in a or '媽的' in a:
            message = "我不講髒話呦喵"
        print("輸出:" + message)
        await ctx.send(message)

    @commands.command()
    async def adminsay(self, ctx, a: str):
        print(a)
        await ctx.message.delete()
        message = a
        if ('http' not in a):
            if ('<:' not in a):
                message += "喵"
        await ctx.send(message)

    @commands.command()
    async def laugh(self, ctx):
        await ctx.send('哈哈...')

    @commands.command()
    async def 測試(self, ctx):
        await ctx.send('你到底想幹嘛')

    @commands.command()
    async def penguinLaugh(self, ctx):

        await ctx.send("""<:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626><:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626><:Penguin:623835905999896626>
<:Penguin:623835905999896626>""")

    @commands.command()
    async def emoji(self, ctx):
        emojiList = self.bot.emojis
        emojiString = "<:"
        emojiString += (emojiList[1].name + ":" + str(emojiList[1].id)) + ">"
        await ctx.send(emojiString)

    @commands.command()
    async def nameOfGuild(self, ctx):
        await ctx.send(ctx.channel.id)

    @commands.command()
    async def test(self, ctx):
        emoji = self.bot.get_emoji(411984275815137290)
        await ctx.message.delete()
        await ctx.send(emoji)

    @commands.command()
    async def hahaha(self, ctx):
        await ctx.send("""HAHAHAHAHAHAHAHAHAHA""")

    @commands.command()
    async def getEmoji(self, ctx):
        emojiList = self.bot.emojis
        emojiString = ""
        for emoji in emojiList:
            emojiString += str(emoji)
        await ctx.send(emojiString)    
    
    @commands.command()
    async def kiang(self,ctx):
        emoji = self.bot.get_emoji(699474147818078358)
        await ctx.message.delete()
        await ctx.send(emoji)
        
    @commands.command()
    async def 摸摸艾路貓(self,ctx):
        """摸摸艾路貓 他會很開心"""
        currectAuthor = str(ctx.author.id)
        self.dbcursor.execute('SELECT * FROM PetCat WHERE userid ="' +currectAuthor+'"')
        #self.dbcursor.execute('SELECT * FROM PetCat')
        temp = self.dbcursor.fetchone()
        petcounttemp = 0
        if temp == None:
            self.dbconnect.execute('INSERT INTO PetCat ("userid","pettime") VALUES ("'+currectAuthor+'",1)')
            petcounttemp = 1
        else:
            (userid,petcount) = temp
            petcounttemp = petcount
            petcounttemp+=1
            self.dbconnect.execute('UPDATE PetCat SET pettime='+str(petcounttemp)+' WHERE userid ="' +currectAuthor+'"')
        self.dbconnect.commit()
        emoji = self.bot.get_emoji(754954248961261658)
        await ctx.send(emoji)
        await ctx.send("你已經摸了艾路貓"+str(petcounttemp)+"次喔")
        
    
    @commands.command()
    async def logout(self, ctx):
        """沒事別用"""
        await ctx.send('我要下線了喵')
        await self.bot.close()

    @commands.command()
    async def quote(self, ctx,a: int,reply:str = ''):
        """特殊Quote 比較漂亮"""
        temp = await ctx.fetch_message(a)
        # message = "> "
        # message += temp.author.display_name + " 說了 " + temp.content
        # if reply != '':
        #     message += "\n\n\n**" + ctx.author.display_name + "回應說:**\n\n" + reply

        embed=discord.Embed(color=temp.author.roles[-1].color)
        embed.add_field(name=temp.content,value=("在"+temp.created_at.astimezone('Asia/Taipei').strftime("%Y-%m-%d %H:%M:%S")), inline=False)

        embed.set_author(name=temp.author.display_name,icon_url=temp.author.avatar_url)
        embed.set_footer(text=("標註者："+ctx.author.display_name))
        await ctx.send(embed=embed)
        #await ctx.send(message)
    
    @commands.command()
    async def otherchannelquote(self, ctx,a: int,b: int):
        """使用方法 $otherchannelquote <頻道ID> <要Quote的訊息ID>"""
        tempchannel = await self.bot.fetch_channel(a)
        temp = await tempchannel.fetch_message(b)
        # message = "> "
        # message += temp.author.display_name + " 說了 " + temp.content
        # if reply != '':
        #     message += "\n\n\n**" + ctx.author.display_name + "回應說:**\n\n" + reply

        embed=discord.Embed(color=temp.author.roles[-1].color)
        embed.add_field(name=temp.content,value=("在"+temp.created_at.astimezone('Asia/Taipei').strftime("%Y-%m-%d %H:%M:%S")), inline=False)
        embed.set_author(name=temp.author.display_name,icon_url=temp.author.avatar_url)
        embed.set_footer(text=("標註者："+ctx.author.display_name))
        await ctx.send(embed=embed)
        #await ctx.send(message)


    @commands.command()
    async def 動彈不得(self, ctx):
        """貓咪會救你 只是可能要等一下"""
        await ctx.channel.send("""主人危險!
主人我來救您了喵!(跑到旁邊喝水""")

    @commands.command()
    async def 激勵邦歌鼓口哨(self, ctx):
        """今天貓咪心情不太好"""
        await ctx.channel.send("""我現在沒空聽從指示啦喵！""")

        # await ctx.send("""主人危險!

    # 主人我來救您了喵!(跑到旁邊喝水""")

    @commands.command(pass_context=True)
    async def ping(self, ctx):
        """ Pong! """
        await ctx.message.delete()
        before = time.monotonic()
        message = await ctx.send("Pong!")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"Pong!  `{int(ping)}ms`")
        print(f'Ping {int(ping)}ms')
        
    @commands.command()
    async def getMessageAuthorID(self,ctx):
        authorID = ctx.author
        print(authorID.id)

    
def setup(bot):
    bot.add_cog(mainCog(bot))
