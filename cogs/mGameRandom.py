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
from discord import app_commands
from static import hpsh, utcs

import urllib.request

class mGameRandom(commands.Cog):

    def __init__(self, bot:commands.Bot):
        self.bot:commands.Bot = bot
        # self.maiData = json.load(open('cogs/asset/text/maimai.json',encoding="utf-8"))
        self.sdvxData = json.load(open('cogs/asset/text/sdvx.json',encoding="utf-8"))
        
        
    # @commands.command()
    @commands.hybrid_command(name='我想打mai',description='隨機挑選一首maimai譜面')
    @app_commands.guilds(hpsh, utcs)
    @app_commands.rename(lv='等級')
    @app_commands.rename(lev_bas='basic')
    @app_commands.rename(lev_adv='advanced')
    @app_commands.rename(lev_exp='expert')
    @app_commands.rename(lev_mas='master')
    @app_commands.rename(lev_rem='remaster')
    async def 我想打mai(self, ctx:commands.Context, lv:str = "", lev_bas:str = "", lev_adv:str = "", lev_exp:str = "", lev_mas:str = "", lev_rem:str = ""):
    # https://maimai.sega.com/assets/data/maimai_songs.json
        # print(self.maiData)
        with urllib.request.urlopen('https://maimai.sega.com/assets/data/maimai_songs.json') as url:
            data = json.loads(url.read().decode())

            for d in data:
                if 'dx_lev_bas' in d.keys():
                    d['lev_bas'] = d['dx_lev_bas']
                    d['lev_adv'] = d['dx_lev_adv']
                    d['lev_exp'] = d['dx_lev_exp']
                    d['lev_mas'] = d['dx_lev_mas']
                    d['is_dx'] = True

                if 'dx_lev_remas' in d.keys():
                    d['lev_remas'] = d['dx_lev_remas']
                    # d['is_dx'] = True

                d['lvs'] = []

                if 'lev_bas' in d.keys():
                    d['lvs'].append(d['lev_bas'])
                    d['lvs'].append(d['lev_adv'])
                    d['lvs'].append(d['lev_exp'])
                    d['lvs'].append(d['lev_mas'])

                if 'lev_remas' in d.keys():
                    d['lvs'].append(d['lev_remas'])

            if not lv == "":
                data = list(filter(lambda x: lv in x['lvs'], data))
            else:
                if not lev_bas == "":
                    data = list(filter(lambda x: lev_bas in x['lev_bas'], data))
                elif not lev_adv == "":
                    data = list(filter(lambda x: lev_adv in x['lev_adv'], data))
                elif not lev_exp == "":
                    data = list(filter(lambda x: lev_exp in x['lev_exp'], data))
                elif not lev_mas == "":
                    data = list(filter(lambda x: lev_mas in x['lev_mas'], data))
                elif not lev_rem == "":
                    data = list(filter(lambda x: lev_rem in x['lev_ult'], data))
            

            temp = random.randint(0,len(data)-1)
            randData = data[temp]
            print(randData)
            # title = randData['name']
            # if randData['type'] == 'DX':
            #     title += ' (DX 譜面)'
            title = randData['title']

            # "lev_bas": "7",
            # "lev_adv": "7+",
            # "lev_exp": "9",
            # "lev_mas": "10+",
            # "lev_remas": "12+",


            basic = ""
            advanced = ""
            expert = ""
            master = ""
            remaster = ""

            if 'lev_bas' in randData.keys():
                basic = randData['lev_bas']

            if 'lev_adv' in randData.keys():
                advanced = randData['lev_adv']

            if 'lev_exp' in randData.keys():
                expert = randData['lev_exp']
            
            if 'lev_mas' in randData.keys():
                master = randData['lev_mas']

            if 'lev_remas' in randData.keys():
                remaster = randData['lev_remas']

            #'dx_lev_bas': '4', 'dx_lev_adv': '7', 'dx_lev_exp': '10+', 'dx_lev_mas': '13',"dx_lev_remas": "13+",
            DX_TEST = ""
            if 'is_dx' in randData.keys():
                DX_TEST = "(DX 譜面)"



            embed=discord.Embed(title=title+DX_TEST,description=randData["artist"])
                
            embed.set_thumbnail(url='https://maimaidx-eng.com/maimai-mobile/img/Music/'+randData['image_url'])
            embed.add_field(name='Basic', value=basic, inline=True)
            embed.add_field(name='Advanced', value=advanced, inline=False)
            embed.add_field(name='Expert', value=expert, inline=False)
            embed.add_field(name='Master', value=master, inline=False)
            if remaster != "":
                embed.add_field(name='Re:Master', value=remaster, inline=False)

            await ctx.send('為您挑選出：',embed=embed)

    @commands.hybrid_command(name='我想打sdvx',description='隨機挑選一首sdvx譜面')
    @app_commands.guilds(hpsh, utcs)
    @app_commands.rename(lv='等級')
    @app_commands.rename(lev_nov='novice')
    @app_commands.rename(lev_adv='advanced')
    @app_commands.rename(lev_exh='exhaust')
    @app_commands.rename(lev_inf='infinite')
    @app_commands.rename(lev_mxm='maximum')
    async def 我想打sdvx(self, ctx:commands.Context, lv:str = "", lev_nov:str = "", lev_adv:str = "", lev_exh:str = "", lev_inf:str = "", lev_mxm:str = ""):
        
        # print(self.sdvxData)
        for d in self.sdvxData["mdb"]["music"]:
            d['lvs'] = []
            d['lvs'].append(d['difficulty']['novice']['difnum']['#text'])
            d['lvs'].append(d['difficulty']['advanced']['difnum']['#text'])
            d['lvs'].append(d['difficulty']['exhaust']['difnum']['#text'])
            if 'infinite' in d['difficulty'].keys():
                if d['difficulty']['infinite']['difnum']['#text'] != 0:
                    d['lvs'].append(d['difficulty']['infinite']['difnum']['#text'])
            if 'maximum' in d['difficulty'].keys():
                if d['difficulty']['maximum']['difnum']['#text'] != 0:
                    d['lvs'].append(d['difficulty']['maximum']['difnum']['#text'])

        data = []


        if not lv == "":
            data = list(filter(lambda x: lv in x['lvs'], self.sdvxData["mdb"]["music"]))
        else:
            if not lev_nov == "":
                data = list(filter(lambda x: lev_nov in x['difficulty']['novice']['difnum']['#text'], self.sdvxData["mdb"]["music"]))
            elif not lev_adv == "":
                data = list(filter(lambda x: lev_adv in x['difficulty']['advanced']['difnum']['#text'], self.sdvxData["mdb"]["music"]))
            elif not lev_exh == "":
                data = list(filter(lambda x: lev_exh in x['difficulty']['exhaust']['difnum']['#text'], self.sdvxData["mdb"]["music"]))
            elif not lev_inf == "":
                data = list(filter(lambda x: lev_inf in x['difficulty']['infinite']['difnum']['#text'], self.sdvxData["mdb"]["music"]))
            elif not lev_mxm == "":
                data = list(filter(lambda x: 'maximum' in x['difficulty'].keys(), self.sdvxData["mdb"]["music"]))
                data = list(filter(lambda x: lev_mxm in x['difficulty']['maximum']['difnum']['#text'], data))

        if len(data) == 0:
            await ctx.send('找不到符合的譜面')
            return

        temp = random.randint(0,len(data)-1)
        randData = data[temp]

        print(randData)
        path = "cogs/asset/img/sdvx/"
        path += "jk_{:04d}_1.png".format(int(randData["@id"]))
        file = discord.File(path,filename='jacket.png')

        color_thief = ColorThief(path)
        dominant_color = color_thief.get_color(quality=1)

        musicName = randData['info']['title_name']
        novice = int(randData['difficulty']['novice']['difnum']['#text'])
        advanced = int(randData['difficulty']['advanced']['difnum']['#text'])
        exhaust = int(randData['difficulty']['exhaust']['difnum']['#text'])
        infinite = int(randData['difficulty']['infinite']['difnum']['#text'])
        maximum = 0
        if 'maximum' in randData['difficulty'].keys():
            maximum = int(randData['difficulty']['maximum']['difnum']['#text'])


        ver = 0

        if 'inf_ver' in randData['info'].keys():
            ver = randData['info']['inf_ver']['#text']

        print(ver)
        inf_text = ""

        if ver == '2':
            inf_text = "INF"
        elif ver == '3':
            inf_text = "GRV"
        elif ver == '4':
            inf_text = "HVN"
        elif ver == '5':
            inf_text = "VVD"
        elif ver == '6':
            inf_text = "XCD"

        

        print(novice,advanced,exhaust,infinite,maximum)

        embed=discord.Embed(title=musicName)
        embed.add_field(name='NOV', value=novice, inline=True)
        embed.add_field(name='ADV', value=advanced, inline=False)
        embed.add_field(name='EXH', value=exhaust, inline=False)
        if infinite != 0:
            embed.add_field(name=inf_text, value=infinite, inline=False)
        if maximum != 0:
            embed.add_field(name='MXM', value=maximum, inline=False)
        embed.set_thumbnail(url='attachment://jacket.png')

        await ctx.send('為您挑選出：',file=file,embed=embed)
    
    @commands.hybrid_command(name='我想打中二',description='隨機挑選一首中二譜面')
    @app_commands.guilds(hpsh, utcs)
    @app_commands.rename(src='來源伺服器')
    @app_commands.describe(src='來源伺服器 預設為國際服')
    @app_commands.choices(src=[
        app_commands.Choice(name="國際服", value=1),
        app_commands.Choice(name="日服", value=2)
    ])
    @app_commands.rename(lv='等級')
    @app_commands.rename(lev_bas='basic')
    @app_commands.rename(lev_adv='advanced')
    @app_commands.rename(lev_exp='expert')
    @app_commands.rename(lev_mas='master')
    @app_commands.rename(lev_ult='ultima')
    async def 我想打中二(self, ctx:commands.Context, src:int = 1, lv:str = "", lev_bas:str = "", lev_adv:str = "", lev_exp:str = "", lev_mas:str = "", lev_ult:str = ""):
        link_src = ""
        
        if src == 1:
            link_src = 'https://chunithm.sega.com/assets/data/music.json'
        elif src == 2:
            link_src = 'https://chunithm.sega.jp/storage/json/music.json'
        
        
        with urllib.request.urlopen(link_src) as url:
            data = json.loads(url.read().decode())
            
            for d in data:
                d['lvs'] = [str(d['lev_bas']),str(d['lev_adv']),str(d['lev_exp']),str(d['lev_mas']),str(d['lev_ult'])]
            
            if not lv == "":
                data = list(filter(lambda x: lv in x['lvs'], data))
            else:
                if not lev_bas == "":
                    data = list(filter(lambda x: lev_bas in x['lev_bas'], data))
                elif not lev_adv == "":
                    data = list(filter(lambda x: lev_adv in x['lev_adv'], data))
                elif not lev_exp == "":
                    data = list(filter(lambda x: lev_exp in x['lev_exp'], data))
                elif not lev_mas == "":
                    data = list(filter(lambda x: lev_mas in x['lev_mas'], data))
                elif not lev_ult == "":
                    data = list(filter(lambda x: lev_ult in x['lev_ult'], data))
            
            if len(data) == 0:
                await ctx.send('沒有符合條件的譜面')
                return
            

            temp = random.randint(0,len(data)-1)
            randData = data[temp]

            musicName = randData['title']

            # "lev_bas": "1",
            # "lev_adv": "5",
            # "lev_exp": "8",
            # "lev_mas": "11",
            # "lev_ult": "",

            basic = randData['lev_bas']
            advanced = randData['lev_adv']
            expert = randData['lev_exp']
            master = randData['lev_mas']
            ultimate = randData['lev_ult']


            embed=discord.Embed(title=musicName)
            embed.add_field(name='Basic', value=basic, inline=True)
            embed.add_field(name='Advanced', value=advanced, inline=False)
            embed.add_field(name='Expert', value=expert, inline=False)
            embed.add_field(name='Master', value=master, inline=False)
            if ultimate != '':
                embed.add_field(name='Ultima', value=ultimate, inline=False)

            if src == 1:
                embed.set_thumbnail(url='https://chunithm-net-eng.com/mobile/img/'+randData['image'])
            elif src == 2:
                embed.set_thumbnail(url='https://new.chunithm-net.com/chuni-mobile/html/mobile/img/'+randData['image'])
                

            await ctx.send('為您挑選出：',embed=embed)
            
async def setup(bot):
    await bot.add_cog(mGameRandom(bot))
