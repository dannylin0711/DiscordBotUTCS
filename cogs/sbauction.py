import json
import multiprocessing
import pathlib
import socket
import time
from static import utcs, hpsh
from typing import List, Literal
import requests


import discord
from discord.ext import commands, tasks
from discord import app_commands, ForumChannel

class MCSBAuction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auction_status = {}
        
    @commands.hybrid_command(name="更新auction", description="")
    @app_commands.guilds(utcs, hpsh)
    async def update_auction(self, ctx):
        # get https://api.hypixel.net/skyblock/auction?key=API_KEY&profile=PROFILE_ID
        # 138e494e-d991-4731-99f7-e52b8d67d763
        try:
            auction_get = requests.get("https://api.hypixel.net/skyblock/auction?key=138e494e-d991-4731-99f7-e52b8d67d763&profile=a10440f6-3109-4f87-83d2-521c1f2c3f65")
        except:
            await ctx.send("更新失敗")
            return
        
        auction_json = auction_get.json()
        self.auction_status = auction_json
        await ctx.send("更新成功")
        
    
    @commands.hybrid_command(name="查詢已賣出", description="")
    @app_commands.guilds(utcs, hpsh)
    async def check_auction(self, ctx):
        if self.auction_status == {}:
            await ctx.send("請先更新auction")
            return
        
        temp = []
        for item in self.auction_status["auctions"]:
            if item["highest_bid_amount"] != 0:
                temp.append(item)
                
        if len(temp) == 0:
            await ctx.send("沒有已賣出的物品")
        else:
            await ctx.send(f"已賣出的物品有{len(temp)}個: {' '.join([item['item_name'] for item in temp])}")
            
    @commands.hybrid_command(name="銀行", description="")
    @app_commands.guilds(utcs, hpsh)
    async def banking(self, ctx):
        # get https://api.hypixel.net/skyblock/auction?key=API_KEY&profile=PROFILE_ID
        # 138e494e-d991-4731-99f7-e52b8d67d763
        try:
            profile_get = requests.get("https://api.hypixel.net/skyblock/profile?key=138e494e-d991-4731-99f7-e52b8d67d763&profile=a10440f6-3109-4f87-83d2-521c1f2c3f65")
        except:
            await ctx.send("更新失敗")
            return
        
        profile_json = profile_get.json()
        banking = profile_json["profile"]["banking"]
        
        await ctx.send("現在有 {:.2f} 元".format(banking["balance"]))
        
            
    
async def setup(bot: commands.Bot):
    await bot.add_cog(MCSBAuction(bot))
        
# VESTA_S bb5a25a6806d460485b80a1c5e4fedd2
# wikii bb76c4513a0f48a2b4337a914af5addb
# dannylin0711 6d593c8cea384fb3b931c6d1e162ff3e