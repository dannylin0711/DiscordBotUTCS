from ctypes import Union
import discord
from discord.ext import commands, tasks
from discord import app_commands
from static import utcs, hpsh
import asyncio
import edge_tts
from threading import Timer
import io
import global_var
import random
from typing import cast
from discord.ext import voice_recv
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests
import base64

API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/4710d1a4bddfa4c8c2dfbc37f7542109/ai/run/"
headers = {"Authorization": "Bearer 7-LBN6A3rtWjuyO0Y_lZPvJ2FXP5B8YWw-wIlQbT"}

class Slash(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.play_silent, 'interval', minutes=1)
        
    def play_silent(self):
        global_var.voice.play(discord.FFmpegPCMAudio("cogs/asset/silent.mp3"))
        
    # @app_commands.command(name="testing")
    @commands.hybrid_command(name="testing_hybrid", with_app_command=True, description="?")
    @app_commands.guilds(utcs, hpsh)
    async def testing(self, ctx: commands.Context) -> None:
        await ctx.send("???")

    @commands.hybrid_command(name="開始練功", with_app_command=True, description="自動計時輪、燒")
    @app_commands.guilds(utcs, hpsh)
    async def 開始練功(self, ctx: commands.Context) -> None:
        k = ctx.message.author.mention
        await ctx.send("{} 開始練功" .format(k))
        self.輪.start(ctx)
        self.燒.start(ctx)

    @commands.hybrid_command(name="結束練功", with_app_command=True, description="自動計時輪、燒")
    @app_commands.guilds(utcs, hpsh)
    async def 結束練功(self, ctx: commands.Context) -> None:
        await ctx.send("結束練功")
        self.輪.stop()
        self.燒.stop()
        
    @tasks.loop(seconds=5)
    async def 輪(self, ctx): # You can pass the `ctx` parameter if you want, but there's no point in doing that
        # channel = self.bot.get_channel(626624763141423134)
        k = ctx.message.author.mention
        await ctx.send("{} 輪的時間到了".format(k))

    @tasks.loop(seconds=10)
    async def 燒(self, ctx): # You can pass the `ctx` parameter if you want, but there's no point in doing that
        # channel = self.bot.get_channel(626624763141423134)
        k = ctx.message.author.mention
        await ctx.send("{} 燒的時間到了".format(k))
        
        
    @commands.hybrid_command(name="美麗的夏洛特庫魯風最終神聖美妙美麗超級麥格農性感十足魅力虛閃復甦", with_app_command=True, description="必殺")
    @app_commands.guilds(utcs, hpsh)
    async def cero(self, ctx: commands.Context) -> None:
       
        if global_var.voice is None:
            global_var.voice = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        else:
            await global_var.voice.disconnect()
            global_var.voice = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        # await ctx.send("必殺")
        await ctx.send("https://tenor.com/view/bleach-thousand-year-blood-war-tybw-cour-2-ironsilver-gif-15602663191967092448")
        await asyncio.sleep(2)
        global_var.voice.play(discord.FFmpegPCMAudio("cogs/asset/cero.mp3", options="-filter:a \"volume=0.3\""))
        await asyncio.sleep(10)
        await global_var.voice.disconnect()
        
    @commands.hybrid_command(name="加入頻道", with_app_command=True, description="加入頻道")
    @app_commands.guilds(utcs, hpsh)
    async def add_channel(self, ctx: commands.Context) -> None:
        if global_var.voice is None:
            global_var.voice = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        else:
            await global_var.voice.disconnect()
            global_var.voice = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
            
        self.scheduler.start()
        
        await ctx.send("已加入頻道", ephemeral=True)
        
    @commands.hybrid_command(name="退出頻道", with_app_command=True, description="退出頻道")
    @app_commands.guilds(utcs, hpsh)
    async def leave_channel(self, ctx: commands.Context) -> None:
        self.scheduler.shutdown()
        
        if global_var.voice is None:
            await ctx.send("請先加入頻道", ephemeral=True)
            return
        else:
            await global_var.voice.disconnect()
        
        await ctx.send("已退出頻道", ephemeral=True)
    
    
    @commands.hybrid_command(name="tts", with_app_command=True, description="TTS")
    @app_commands.guilds(utcs, hpsh)
    @app_commands.rename(text='轉語音文字')
    @app_commands.rename(voice='聲音')
    @app_commands.describe(voice="1, 2, 3")
    async def tts(self, ctx: commands.Context, text:str, voice:int) -> None:
        # in_voice = ""
        # if voice == 1:
        #     in_voice = "zh-TW-HsiaoChenNeural"
        # elif voice == 2:
        #     in_voice = "zh-TW-HsiaoYuNeural"
        # else:
        #     in_voice = "zh-TW-YunJheNeural"
        
        # communicate = edge_tts.Communicate(text, in_voice)
        
        # audio = io.BytesIO()
        # async for chunk in communicate.stream():
        #     if chunk["type"] == "audio":
        #         audio.write(chunk["data"])
        
        # audio.seek(0)
        if global_var.voice is None:
            await ctx.send("請先加入頻道", ephemeral=True)
            return
        i = { "prompt": text,
             "lang": "ZH"
            #  "stream": True
             }
        response = requests.post(f"{API_BASE_URL}@cf/myshell-ai/melotts", headers=headers, json=i)
        audio = io.BytesIO(base64.b64decode(response.json()["result"]["audio"]))
        # file = discord.File(image_data, filename="image.png")
        # await ctx.send(file=file)
        
        
        global_var.voice.play(discord.FFmpegPCMAudio(audio, pipe=True, options="-filter:a \"volume=0.3\""))
                    
        await ctx.send("已執行指令", ephemeral=True)
        
    @commands.hybrid_command(name="setrecordtarget", with_app_command=True, description="record")
    @app_commands.guilds(utcs, hpsh)
    async def setrecordtarget(self, ctx: commands.Context) -> None:
        if global_var.voice is None:
            await ctx.send("請先加入頻道", ephemeral=True)
            return
        
        current_connected_members = global_var.voice.channel.members
        
        selection = discord.ui.Select(placeholder="請選擇用戶", min_values=1, max_values=1)
        
        for member in current_connected_members:
            selection.add_option(label=member.display_name, value=member.id)
            
        async def selection_callback(interaction: discord.Interaction):
            selected_id = interaction.data["values"][0]
            global_var.record_target.append(int(selected_id))
            print(global_var.record_target)
            await interaction.response.send_message("已新增{}".format(interaction.data["values"][0]), ephemeral=True)
        
        selection.callback = selection_callback
        
        view = discord.ui.View()
        view.add_item(selection)
        
        await ctx.send("請選擇用戶", view=view, ephemeral=True)
        
    @commands.hybrid_command(name="removerecordtarget", with_app_command=True, description="record")
    @app_commands.guilds(utcs, hpsh)
    async def removerecordtarget(self, ctx: commands.Context) -> None:
        
        
        selection = discord.ui.Select(placeholder="請選擇用戶", min_values=1, max_values=1)
        
        for id in global_var.record_target:
            member = await ctx.bot.fetch_user(id)
            selection.add_option(label=member.display_name, value=id)
            
        async def selection_callback(interaction: discord.Interaction):
            selected_id = interaction.data["values"][0]
            global_var.record_target.remove(int(selected_id))
            await interaction.response.send_message("已選擇{}".format(interaction.data["values"][0]), ephemeral=True)
        
        selection.callback = selection_callback
        
        view = discord.ui.View()
        view.add_item(selection)
        
        await ctx.send("請選擇用戶", view=view, ephemeral=True)
        
    
        
    @commands.hybrid_command(name="record", with_app_command=True, description="record")
    @app_commands.guilds(utcs, hpsh)
    async def record(self, ctx: commands.Context) -> None:
        if global_var.voice is None:
            await ctx.send("請先加入頻道", ephemeral=True)
            return
        
        def callback(user, data:voice_recv.VoiceData):
            print(user, data)
        
        buffer = io.BytesIO()
        
        global_var.voice.listen(CustomWavAudioSink("{}.wav".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))))
        await ctx.send("已開始錄音", ephemeral=True)
    
    @commands.hybrid_command(name="stop_record", with_app_command=True, description="record")
    @app_commands.guilds(utcs, hpsh)
    async def stop_record(self, ctx: commands.Context) -> None:
        if global_var.voice is None:
            await ctx.send("請先加入頻道", ephemeral=True)
        
        global_var.voice.stop_listening()
        await ctx.send("已停止錄音", ephemeral=True)
        
    @commands.hybrid_command(name="capture_mode", with_app_command=True, description="用了這個指令就會無時無刻監聽你的文字，並用TTS轉傳到語音中")
    @app_commands.guilds(utcs, hpsh)
    async def capture_mode(self, ctx: commands.Context, switch: bool) -> None:
        if switch:
        
            
            global_var.global_listener[ctx.author.id] = 1 #random.randint(-200, 200)
            await ctx.send("已啟用完全擷取模式 您這次使用的頻率offset為{}".format(global_var.global_listener[ctx.author.id]), ephemeral=True)
        else:
            global_var.global_listener.pop(ctx.author.id)
            await ctx.send("已關閉完全擷取模式", ephemeral=True)

        
async def setup(bot: commands.Bot):
    await bot.add_cog(Slash(bot))
    
log = logging.getLogger(__name__)

import wave
from discord.opus import Decoder as OpusDecoder
from discord import User
from typing import Optional, Union
from discord.ext.voice_recv import AudioSink, VoiceData
from typing import TypedDict
import os
class CustomWavAudioSink(AudioSink):
    # override init, passthrough
    
    CHANNELS = OpusDecoder.CHANNELS
    SAMPLE_WIDTH = OpusDecoder.SAMPLE_SIZE // OpusDecoder.CHANNELS
    SAMPLING_RATE = OpusDecoder.SAMPLING_RATE
    def __init__(self, destination: str):
        super().__init__()

        # self._file: wave.Wave_write = wave.open(destination, 'wb')
        # self._file.setnchannels(self.CHANNELS)
        # self._file.setsampwidth(self.SAMPLE_WIDTH)
        # self._file.setframerate(self.SAMPLING_RATE)
        
        self._file: dict[str, wave.Wave_write] = {}
        
        for i in global_var.record_target:
            if os.path.exists("recording/") == False:
                os.makedirs("recording/")
            
            if os.path.exists("recording/{}/".format(i)) == False:
                os.makedirs("recording/{}/".format(i))            
            
            self._file[str(i)] = wave.open(str("recording/{}/".format(i)+destination), 'wb')
        
        for file in self._file.values():
            file.setnchannels(self.CHANNELS)
            file.setsampwidth(self.SAMPLE_WIDTH)
            file.setframerate(self.SAMPLING_RATE)
        
        

    def wants_opus(self) -> bool:
        return False

    def write(self, user: Optional[User], data: VoiceData) -> None:
        # print(user, data)
        if user.id in global_var.record_target:
            # print(user, data)
            self._file[str(user.id)].writeframes(data.pcm)
        
        

    def cleanup(self) -> None:
        try:
            for i in self._file.values():
                i.close()
        except Exception:
            log.warning("WaveSink got error closing file on cleanup", exc_info=True)
        
    
    