import json
import sqlite3
import discord
import os
import datetime
import re
import requests
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get
from discord import Guild
from discord import Client
from discord import opus
from static import guildListList
import global_var
import asyncio
import edge_tts
import io

import discord
from discord.ext import commands, tasks
from discord import app_commands, ForumChannel

from static import utcs, hpsh

class Events(commands.Cog):
    VOCABS_URL = "https://invade.tw/assets/scripts/db_vocabs.js"

    @commands.Cog.listener()
    async def on_message(self,message: discord.Message):
    # we do not want the bot to reply to itself
        if message.channel.id == 1239392427811536937:# and message.author.id == 1239392487722844190:
            await message.publish()

        if message.author == self.bot.user:
            return
        if 'RRRR' in message.content:
            emoji = self.bot.get_emoji(623835905999896626)
            await message.add_reaction(emoji)
            
        # find if any vocab is in the message
        # if self.vocabs is not None:
        #     find_result = [x[0] in message.content for x in self.vocabs]
        #     if any(find_result):
        #         matched_vocab = self.vocabs[find_result.index(True)]
        #         message_find = f"逼逼！支語警察關心您，您剛剛使用了支語「{matched_vocab[0]}」，請注意您的用詞喵！"
        #         await message.reply(message_find, mention_author=False)
            
            
        temp = message.content.replace(" ","")
        if 'ㄎㄧㄤ' in temp:
            emoji = self.bot.get_emoji(699474147818078358)
            await message.add_reaction(emoji)
             
        await self.check_trigger(temp, message)
        
        if message.author.id in global_var.global_listener:
            if global_var.voice is None:
                await message.add_reaction('❌')
                await asyncio.sleep(0.5)
                await message.remove_reaction('❌',self.bot.user)
                return
            
            await message.add_reaction('📣')
            await asyncio.sleep(0.5)
            await message.remove_reaction('📣',self.bot.user)
            pitch = global_var.global_listener[message.author.id]
            pitch_value = "+{}Hz".format(pitch) if pitch > 0 else "{}Hz".format(pitch)
            communicate = edge_tts.Communicate(message.content , "zh-TW-HsiaoChenNeural", pitch=pitch_value)
        
            audio = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio.write(chunk["data"])
            
            audio.seek(0)
            
            
            global_var.voice.play(discord.FFmpegPCMAudio(audio, pipe=True, options="-filter:a \"volume=0.3\""))
        
    async def check_trigger(self, trigger_check_str: str , message: discord.Message):
        # Match when the MESSAGE contains a stored trigger.
        # Use a parameterized query to avoid quote/% issues.
        trigger_check_str_trimmed = trigger_check_str.replace("mygo","").strip()
                
        row = self.dbcursor.execute(
            "SELECT trigger, link FROM comb WHERE instr(?, trigger) > 0 ORDER BY length(trigger) DESC LIMIT 1",
            (trigger_check_str_trimmed,),
        ).fetchone()

        if row is not None and "mygo" in trigger_check_str:
            await message.channel.send(row["link"])
        
        test = filter(lambda x: x["name"] == trigger_check_str_trimmed, self.json)
        if len(list(test)) != 0 and "mygo" in trigger_check_str:
            await message.channel.send(file=discord.File(f'./cogs/asset/img/mygo/{trigger_check_str_trimmed}.jpg'))

         
        
    @commands.Cog.listener()
    async def on_ready(self):
        print('Logged in as')
        print(self.bot.user.name)
        print(self.bot.user.id)
        print('------')
        # activity = discord.Streaming(name='當一隻艾路貓',url='https://www.twitch.tv/dannylin0711')
        # activity.game = "Monster Hunter World"
        # emoji = self.bot.get_emoji(1109419887371231292)
        # emoji = discord.PartialEmoji.from_str('')
        activity = discord.CustomActivity(name='🐱當一隻艾路貓')
        await self.bot.change_presence(status=discord.Status.online,activity=activity)
        
        # await self.bot.tree.sync(guilds = [discord.Object(id = 516470319242805264), discord.Object(id = 406411335778304000)])
        for g in guildListList:
            await self.bot.tree.sync(guild = g)
            print(f"Synced slash command for {self.bot.user} in {g.id}.")
        
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
            me = await self.bot.fetch_user(201293557544255488)    
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
            tmessage += "　原訊息內容:"+ before.content + "\n"
            tmessage += "　修改後內容:"+ after.content
        
            if before.content != after.content:
                me = await self.bot.fetch_user(201293557544255488)  
                await me.send(str(tmessage))
                
    @commands.hybrid_command(name="設定對應")
    @app_commands.guilds(utcs, hpsh)
    async def comb(self, ctx: commands.Context, trigger_str: str, link: str) -> None:
        trigger_str = re.sub(r"\s+", "", trigger_str)
        if not trigger_str:
            await ctx.send("觸發字串不能為空")
            return

        # check if trigger_str is already in the database
        check_if_exist = self.dbcursor.execute('SELECT 1 FROM comb WHERE trigger = ?', (trigger_str,))
        if check_if_exist.fetchone() is not None:
            await ctx.send("此觸發字串已存在")
            return
        
        self.dbcursor.execute('INSERT INTO comb (trigger, link) VALUES (?, ?)', (trigger_str, link))
        self.dbconnect.commit()
        
        await ctx.send(f"已新增對應：\n```\n{trigger_str} -> {link}\n```")
    
    @commands.hybrid_command(name="刪除對應")
    @app_commands.guilds(utcs, hpsh)
    async def del_comb(self, ctx: commands.Context, trigger_str: str) -> None:
        trigger_str = re.sub(r"\s+", "", trigger_str)
        if not trigger_str:
            await ctx.send("觸發字串不能為空")
            return

        check_if_exist = self.dbcursor.execute('SELECT 1 FROM comb WHERE trigger = ?', (trigger_str,))
        if check_if_exist.fetchone() is None:
            await ctx.send("此觸發字串不存在")
            return
        
        self.dbcursor.execute('DELETE FROM comb WHERE trigger = ?', (trigger_str,))
        self.dbconnect.commit()
        
        await ctx.send(f"已刪除對應：\n```\n{trigger_str}\n```")
        
    @commands.hybrid_command(name="查看對應")
    @app_commands.guilds(utcs, hpsh)
    async def view_comb(self, ctx: commands.Context) -> None:
        check_all = self.dbcursor.execute('SELECT trigger, link FROM comb ORDER BY trigger COLLATE NOCASE')
        all_comb = check_all.fetchall()
        if len(all_comb) == 0:
            await ctx.send("目前沒有任何對應")
            return

        lines = [f'{row["trigger"]} -> {row["link"]}' for row in all_comb]

        header = f"目前的對應（{len(lines)} 筆）："

        # Discord message limit is 2000 chars; keep a safety margin.
        max_len = 1900
        chunk = ""
        first = True
        for line in lines:
            # +1 for the newline
            if len(chunk) + len(line) + 1 > max_len:
                prefix = header + "\n" if first else ""
                await ctx.send(prefix + "```\n" + chunk.rstrip() + "\n```")
                first = False
                chunk = ""
            chunk += line + "\n"

        if chunk.strip():
            prefix = header + "\n" if first else ""
            await ctx.send(prefix + "```\n" + chunk.rstrip() + "\n```")
        
    
    def __init__(self,bot):
        self.bot = bot
        self.dbconnect = sqlite3.connect('cogs/asset/disp.db')
        self.dbconnect.row_factory = sqlite3.Row
        self.dbcursor = self.dbconnect.cursor()
        print('已載入GIFJPG對應資料庫')
        
        self.json = json.loads(open('cogs/asset/image_map.json').read())
        self.vocabs: list | None = None
        self.vocabs_last_fetch = None
        
        self._vocabs_task = asyncio.create_task(self.refresh_vocabs())

    def _fetch_vocabs_sync(self):
        headers = {
            "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Linux\"",
            "Referer": "https://invade.tw/vocabs?",
        }
        response = requests.get(self.VOCABS_URL, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.text

    async def refresh_vocabs(self):
        try:
            raw_text = await asyncio.to_thread(self._fetch_vocabs_sync)
            raw_text = raw_text.replace('var db_vocabs = ', '')
            self.vocabs = json.loads(raw_text)
            if self.vocabs is None:
                print("Failed to parse db_vocabs.js into JSON; raw text cached.")
            else:
                print("db_vocabs.js fetched and parsed into memory cache.")
                print("Total vocabs loaded:", len(self.vocabs))
        except Exception as exc:
            print(f"Failed to fetch db_vocabs.js: {exc}")
    
    def cog_unload(self):
        self.dbconnect.close()
        print('已卸載GIFJPG對應資料庫')
        
async def setup(bot):
    await bot.add_cog(Events(bot))