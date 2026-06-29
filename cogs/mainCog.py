import asyncio
import datetime
import io
import json
import os
import re
import sqlite3
import time
from datetime import timedelta, timezone

import discord
import pytz
import requests
from discord import VoiceClient, app_commands
from discord.ext import commands
from discord.ext.commands import Bot

# import googletrans
from groq import DefaultAioHttpClient
from groq import AsyncGroq as Groq
from opencc import OpenCC
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageTransform

import global_var
from static import hpsh, utcs
import numpy

def find_coeffs(pa, pb):
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

    A = numpy.matrix(matrix, dtype=float)
    B = numpy.array(pb).reshape(8)

    res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
    return numpy.array(res).reshape(8)


startuptime = datetime.datetime.now()

API_BASE_URL = (
    "https://api.cloudflare.com/client/v4/accounts/4710d1a4bddfa4c8c2dfbc37f7542109/ai/run/"
)
headers = {"Authorization": "Bearer 7-LBN6A3rtWjuyO0Y_lZPvJ2FXP5B8YWw-wIlQbT"}

cc = OpenCC("s2twp")

# translator = googletrans.Translator()


class mainCog(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.dbconnect = sqlite3.connect("petcat.db")
        self.dbcursor = self.dbconnect.cursor()
        print("已載入好感度資料庫")

    # await bot.get_channel(516470319242805272).send('我來嘍喵~')
    @commands.command()
    async def add(self, ctx, a: int, b: int):
        """加法 兩個數字相加 用法: $add a b
        輸出a+b"""
        await ctx.send(a + b)

    @commands.hybrid_command(name="說話", description="讓機器人說話 因為是艾路貓所以會在尾巴說喵")
    @app_commands.guilds(utcs, hpsh)
    @app_commands.rename(a="要說的話")
    async def 說話(self, ctx: commands.Context, a: str):
        """讓機器人說話 因為是艾路貓所以會在尾巴說喵"""

        temp = a
        tempa = False
        tempb = False
        print(temp)
        if "?" in temp:
            temp.translate({ord("?"): None})
            tempa = True
        if "!" in temp:
            temp.translate({ord("!"): None})
            tempb = True
        print(temp)
        message = temp
        print("輸入:" + temp)
        # await ctx.message.delete()

        if "http" not in temp and "<:" not in temp:
            message += "喵"

        if tempa:
            message += "?"

        if tempb:
            message += "!"

        if "主人" in temp:
            message = "你才不是主人呢"

        if "啥小" in temp or "幹" in temp or "媽的" in temp:
            message = "我不講髒話呦喵"

        print("輸出:" + message)
        await ctx.send(message)

    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="聊天", description="跟艾路貓聊天，預設使用Gemma 7B模型進行聊天", with_app_command=True)
    @app_commands.rename(a="要說的話")
    # @app_commands.rename(b='是否要翻譯')
    @app_commands.rename(local="是否使用deepseek-r1")
    async def 聊天(self, ctx: commands.Context, a: str, local: bool = False):
        await ctx.defer()
        inputs = [
            {
                "role": "system",
                "content": "你是一款超級聊天機器貓，你必須依照詢問的問題或是語句做出詳細且合理的回答，但你的回答中不可以出現任何的表情符號，可以包含換行或是粗體等等格式，輸出時請使用Markdown格式，回答時必須使用台灣繁體中文，可以適當的地方加上喵。",
            },
            {"role": "user", "content": a},
        ]

        response = None
    # if local:
        fir = True
        mes = None
        res = ""
        # mes = await ctx.defer()
        async with Groq(
            api_key="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",
            http_client=DefaultAioHttpClient(),
        ) as groq_client:
        

            result = await groq_client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一款超級聊天機器貓，你必須依照詢問的問題或是語句做出詳細且合理的回答，但你的回答中不可以出現任何的表情符號，可以包含換行或是粗體等等格式，輸出時請使用Markdown格式，回答時必須使用台灣繁體中文，可以適當的地方加上喵。",
                    },
                    {"role": "user", "content": a},
                ],
                stream=True,
                max_completion_tokens=8192,
                max_tokens=8192
            )
            
            res = ""
            
            async for chunk in result:
                # print(chunk.choices[0].delta)
                if chunk.choices[0].delta.content is not None:
                    res = res + chunk.choices[0].delta.content
                    # print(res)
                    # if fir:
                    #     mes = await ctx.send(res)
                    #     fir = False
                    # else:
                    #     await mes.edit(content=res)
            # print(result.choices[0].message.content)
            # if fir:
            # fir = False
            # res = ""
            # if result.choices[0].message.content is not None:
            #     res = "A: \n" + result.choices[0].message.content
                # mes = await ctx.send(res)∂
            # else:
            # res = res + result
            # await mes.edit(content=res)
            
            

            res = re.sub(r'<think>.*?</think>', '', res, flags=re.DOTALL).strip()

            if len(res) > 2000:
                with io.BytesIO(res.encode()) as file:
                    await ctx.send(file=discord.File(file, "response.txt"))
            else:
                await ctx.send(res)

            # await mes.edit(content=res)

            # if not response['success']:
            #     await ctx.send("我現在有點忙喵 等等再來找我聊天吧喵")
            #     return

            # text = response["message"]["content"]

            # # if not b:
            # await ctx.send(text)
            # return

            # trans = translator.translate(text, src='en', dest='zh-tw')

            # await ctx.send(trans.text)
        # else:
        #     i = {
        #         "messages": inputs,
        #         #  "stream": True
        #     }
        #     response = requests.post(
        #         f"{API_BASE_URL}@hf/google/gemma-7b-it", headers=headers, json=i
        #     )

        #     print(response.json())
        #     if not response.json()["success"]:
        #         await ctx.send("我現在有點忙喵 等等再來找我聊天吧喵")
        #         return

        #     text = response.json()["result"]["response"]

        #     # if not b:
        #     await ctx.send(text)
        #     return

            # trans = translator.translate(text, src='en', dest='zh-tw')

            # await ctx.send(trans.text)

    @commands.hybrid_command(name="畫畫", description="讓艾路貓畫畫")
    @app_commands.guilds(utcs, hpsh)
    @app_commands.rename(a="要畫的東西")
    async def 畫畫(self, ctx: commands.Context, a: str):
        await ctx.defer()
        # inputs = [
        #     { "role": "system", "content": "你是一款超級聊天機器人，你必須依照詢問的問題或是語句做出詳細且合理的回答，但你的回答中不可以出現任何的表情符號，可以包含換行或是粗體等等格式，輸出時請使用Markdown格式" },
        #     { "role": "user", "content": a},
        # ]
        i = {
            "prompt": a,
            #  "stream": True
        }
        response = requests.post(
            f"{API_BASE_URL}@cf/stabilityai/stable-diffusion-xl-base-1.0", headers=headers, json=i
        )
        image_data = io.BytesIO(response.content)
        file = discord.File(image_data, filename="image.png")
        await ctx.send(file=file)

    @commands.command()
    async def adminsay(self, ctx, a: str):
        print(a)
        await ctx.message.delete()
        message = a
        if "http" not in a:
            if "<:" not in a:
                message += "喵"
        await ctx.send(message)

    @commands.command()
    async def laugh(self, ctx):
        await ctx.send("哈哈...")

    @commands.command()
    async def 測試(self, ctx):
        await ctx.send("你到底想幹嘛")

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
    async def kiang(self, ctx):
        emoji = self.bot.get_emoji(699474147818078358)
        await ctx.message.delete()
        await ctx.send(emoji)

    # @commands.hybrid_command(
    # # @commands.command()
    @commands.hybrid_command(
        name="摸摸艾路貓", with_app_command=True, description="摸摸艾路貓 他會很開心"
    )
    @app_commands.guilds(utcs, hpsh)
    async def 摸摸艾路貓(self, ctx):
        """摸摸艾路貓 他會很開心"""
        currectAuthor = str(ctx.author.id)
        self.dbcursor.execute('SELECT * FROM PetCat WHERE userid ="' + currectAuthor + '"')
        # self.dbcursor.execute('SELECT * FROM PetCat')
        temp = self.dbcursor.fetchone()
        petcounttemp = 0
        if temp == None:
            self.dbconnect.execute(
                'INSERT INTO PetCat ("userid","pettime") VALUES ("' + currectAuthor + '",1)'
            )
            petcounttemp = 1
        else:
            (userid, petcount) = temp
            petcounttemp = petcount
            petcounttemp += 1
            self.dbconnect.execute(
                "UPDATE PetCat SET pettime="
                + str(petcounttemp)
                + ' WHERE userid ="'
                + currectAuthor
                + '"'
            )
        self.dbconnect.commit()
        emoji = self.bot.get_emoji(754954248961261658)
        await ctx.send(emoji)
        await ctx.send("你已經摸了艾路貓" + str(petcounttemp) + "次喔")

    @commands.hybrid_command(
        name="摸摸排行榜", with_app_command=True, description="摸摸艾路貓 看誰摸最多次~"
    )
    @app_commands.guilds(utcs, hpsh)
    async def 摸摸排行榜(self, ctx):
        """摸摸艾路貓 看誰摸最多次~"""
        # currectAuthor = str(ctx.author.id)
        # self.dbcursor.execute('SELECT * FROM PetCat WHERE userid ="' + currectAuthor + '"')
        self.dbcursor.execute("SELECT * FROM PetCat")
        petList = self.dbcursor.fetchall()

        sortedPetList = sorted(petList, key=lambda x: x[1], reverse=True)

        st = "摸摸排行榜\n"
        for pet in sortedPetList:
            # print(pet)
            temp: discord.Member = await self.bot.fetch_user(pet[0])

            st += temp.display_name + "#" + temp.discriminator + " 摸了" + str(pet[1]) + "次\n"
            # print(temp.display_name+"#" + temp.discriminator)

        await ctx.send(st)
        # temp = self.dbcursor.fetchone()
        # petcounttemp = 0
        # if temp == None:
        #     self.dbconnect.execute('INSERT INTO PetCat ("userid","pettime") VALUES ("' + currectAuthor + '",1)')
        #     petcounttemp = 1
        # else:
        #     (userid, petcount) = temp
        #     petcounttemp = petcount
        #     petcounttemp += 1
        #     self.dbconnect.execute(
        #         'UPDATE PetCat SET pettime=' + str(petcounttemp) + ' WHERE userid ="' + currectAuthor + '"')
        # self.dbconnect.commit()
        # emoji = self.bot.get_emoji(754954248961261658)
        # await ctx.send(emoji)
        # await ctx.send("你已經摸了艾路貓" + str(petcounttemp) + "次喔")

    @commands.command()
    async def logout(self, ctx):
        """沒事別用"""
        await ctx.send("我要下線了喵")
        await self.bot.close()

    @commands.command()
    async def quote(self, ctx, a: int, reply: str = ""):
        """特殊Quote 比較漂亮"""
        temp = await ctx.fetch_message(a)
        tempguild = self.bot.get_guild(temp.guild.id)
        this_message_author = await tempguild.fetch_member(temp.author.id)
        print(this_message_author)
        # message = "> "
        # message += temp.author.display_name + " 說了 " + temp.content
        # if reply != '':
        #     message += "\n\n\n**" + ctx.author.display_name + "回應說:**\n\n" + reply

        tempmessage = temp.created_at
        tempmessage = tempmessage.replace(tzinfo=pytz.UTC)
        embed = discord.Embed(color=this_message_author.roles[-1].color)
        embed.add_field(
            name=temp.content,
            value=(
                "在"
                + tempmessage.astimezone(timezone(offset=timedelta(hours=8))).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ),
            inline=False,
        )

        embed.set_author(
            name=this_message_author.display_name, icon_url=this_message_author.avatar_url
        )
        embed.set_footer(text=("標註者：" + ctx.author.display_name))
        await ctx.send(embed=embed)
        # await ctx.send(message)

    @commands.command()
    async def otherchannelquote(self, ctx, a: int, b: int):
        """使用方法 $otherchannelquote <頻道ID> <要Quote的訊息ID>"""
        tempchannel = await self.bot.fetch_channel(a)
        temp = await tempchannel.fetch_message(b)
        tempguild = self.bot.get_guild(temp.guild.id)
        this_message_author = await tempguild.fetch_member(temp.author.id)
        print(this_message_author)
        # message = "> "
        # message += temp.author.display_name + " 說了 " + temp.content
        # if reply != '':
        #     message += "\n\n\n**" + ctx.author.display_name + "回應說:**\n\n" + reply

        tempmessage = temp.created_at
        tempmessage = tempmessage.replace(tzinfo=pytz.UTC)
        embed = discord.Embed(color=this_message_author.roles[-1].color)
        embed.add_field(
            name=temp.content,
            value=(
                "在"
                + tempmessage.astimezone(timezone(offset=timedelta(hours=8))).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ),
            inline=False,
        )

        embed.set_author(
            name=this_message_author.display_name, icon_url=str(this_message_author.avatar)
        )
        embed.set_footer(text=("標註者：" + ctx.author.display_name))
        await ctx.send(embed=embed)
        # await ctx.send(message)

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

    @commands.command()
    async def 我要一杯珍珠奶茶(self, ctx):
        await ctx.send("我們沒有賣珍珠奶茶喔~")

    @commands.command()
    async def 我要一杯QQㄋㄟㄋㄟ好喝到咩噗茶(self, ctx):
        await ctx.send("珍奶 正常微冰")

    @commands.hybrid_command(with_app_command=True, description="P A D O R U")
    @app_commands.guilds(utcs, hpsh)
    async def padoru(self, ctx, test_date: str = ""):
        if test_date:
            temptime = datetime.datetime.strptime(test_date, "%Y-%m-%d")
        else:
            temptime = datetime.datetime.now(pytz.timezone("Asia/Taipei"))
        temptimeyear = temptime.strftime("%Y")
        temptime = datetime.datetime.strptime(temptime.strftime("%m-%d"), "%m-%d")
        christmas = datetime.datetime.strptime("12-25", "%m-%d")
        christmas_date_string = christmas.strftime("%m-%d")
        temptime_date_string = temptime.strftime("%m-%d")
        if christmas_date_string == temptime_date_string:
            author_in_channel = ctx.author.voice.channel is not None

            async def handle_voice():
                if author_in_channel:
                    if global_var.voice is None:
                        global_var.voice = await ctx.author.voice.channel.connect()
                    else:
                        await global_var.voice.disconnect()
                        global_var.voice = await ctx.author.voice.channel.connect()
                    global_var.voice.play(
                        discord.FFmpegPCMAudio(
                            "cogs/asset/hashiresoriyo.mp3", options='-filter:a "volume=0.15"'
                        )
                    )
                    await asyncio.sleep(12)
                    await global_var.voice.disconnect()

            async def send_messages():
                await asyncio.sleep(1)
                await ctx.message.channel.send("走れそりを")
                await asyncio.sleep(2)
                await ctx.message.channel.send("風のように")
                await asyncio.sleep(2)
                await ctx.message.channel.send("つきみはらを")
                await asyncio.sleep(2)
                await ctx.message.channel.send("パドル　パドル")

            await asyncio.gather(handle_voice(), send_messages())
        else:
            if temptime < christmas:
                delta = christmas - temptime
                print(delta.days)
                img = Image.open("cogs/asset/padoru.png")
                font = ImageFont.truetype("cogs/asset/BERNHC.TTF", 56)
                
                text_width = int(font.getlength(str(delta.days)))
                
                temp_size = (200, 80)
                txt_img = Image.new('RGBA', temp_size, (255, 255, 255, 0))
                d = ImageDraw.Draw(txt_img)
                d.text((0, 0), str(delta.days), font=font, fill=(120, 5, 11, 255))
                coeffs = find_coeffs(
                    [(0, 0), (50, 0), (70, 67), (20, 80)],
                    [(0, 0), (text_width, 0), (text_width, 80), (0, 80)],
                ).tolist()
                txt_img = txt_img.transform((temp_size[0], temp_size[1]), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
                txt_img.show()
                
                paste_x = 66
                paste_y = 133
                
                img.paste(txt_img, (paste_x, paste_y), txt_img)
                arr = io.BytesIO()
                img.save(arr, format="PNG")
                arr.seek(0)
                file = discord.File(arr)
                file.filename = "file.png"
                await ctx.send(file=file)
            else:
                temptime = datetime.datetime.strptime(
                    temptimeyear + temptime.strftime("-%m-%d"), "%Y-%m-%d"
                )
                temptimeyearint = int(temptimeyear) + 1
                christmas = datetime.datetime.strptime(str(temptimeyearint) + "-12-25", "%Y-%m-%d")
                delta = christmas - temptime

                img = Image.open("cogs/asset/padoru.png")
                # font = ImageFont.truetype("C:/Windows/Fonts/Broadw.ttf", 25)
                font = ImageFont.truetype("cogs/asset/BERNHC.TTF", 56)
                text_width = int(font.getlength(str(delta.days)))
                
                temp_size = (200, 80)
                txt_img = Image.new('RGBA', temp_size, (255, 255, 255, 0))
                d = ImageDraw.Draw(txt_img)
                d.text((0, 0), str(delta.days), font=font, fill=(120, 5, 11, 255))
                coeffs = find_coeffs(
                    [(0, 0), (50, 0), (70, 67), (20, 80)],
                    [(0, 0), (text_width, 0), (text_width, 80), (0, 80)],
                ).tolist()
                txt_img = txt_img.transform((temp_size[0], temp_size[1]), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
                txt_img.show()
                
                paste_x = 66
                paste_y = 133
                
                img.paste(txt_img, (paste_x, paste_y), txt_img)
                arr = io.BytesIO()
                img.save(arr, format="PNG")
                arr.seek(0)
                file = discord.File(arr)
                file.filename = "file.png"
                await ctx.send(file=file)
                # print(delta.days)

    @commands.command()
    async def lmgtfy(self, ctx, *args):
        temp = "{}".format("+".join(args))
        string = "http://letmegooglethat.com/?q=" + temp
        await ctx.send(string)

    @commands.command()
    async def peko(self, ctx):
        await ctx.send("peko↗peko↘peko↗peko↘peko↗peko↘peko↗peko↘")

    @commands.command()
    async def ping(self, ctx):
        """Pong!"""
        await ctx.message.delete()
        before = time.monotonic()
        message = await ctx.send("Pong!")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"Pong!  `{int(ping)}ms`")
        print(f"Ping {int(ping)}ms")

    @commands.command()
    async def getMessageAuthorID(self, ctx):
        authorID = ctx.author
        print(authorID.id)

    @commands.command()
    async def sync(self, ctx):
        guild = ctx.guild
        await self.bot.tree.sync(guild=guild)
        await self.bot.tree.sync()
        await ctx.send("Command Synced")

    # @commands.command()
    # async def getAll(self, ctx):
    #     l = self.bot.get_command('testing')
    #     await ctx.send(l)


async def setup(bot):
    await bot.add_cog(mainCog(bot))
