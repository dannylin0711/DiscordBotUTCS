import json
import multiprocessing
import pathlib
import socket
import time
from static import utcs, hpsh
from typing import List, Literal
import requests
from bs4 import BeautifulSoup

import discord
from discord.ext import commands, tasks
from discord import app_commands, ForumChannel
import os
import random
from typing import cast
import sqlite3

class ColorChanger(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        # use sqlite3
        self.dbconnect = sqlite3.connect('cogs/asset/color.db')
        self.dbcursor = self.dbconnect.cursor()
        print('已載入顏色資料庫')
        
    # override the cog_unload method
    def cog_unload(self):
        self.dbconnect.close()
        print('已卸載顏色資料庫')
        
    @commands.hybrid_command(name="自訂顏色")
    @app_commands.guilds(utcs, hpsh)
    @app_commands.rename(color="顏色")
    async def color(self, ctx: commands.Context, color: str = "NONE") -> None:
        issued_guild = ctx.guild
        if issued_guild is None:
            await ctx.send("請在伺服器內使用此指令")
            return
        
        current_user_color = self.dbcursor.execute(f'SELECT color_hex FROM color WHERE user_id = {ctx.author.id} AND guild_id = {issued_guild.id}').fetchone()
        
        if current_user_color is not None:
            await ctx.send("你已經有顏色了，請先使用 `/清除顏色`")
            return
        
        if issued_guild == "ERROR":
            await ctx.send("請在伺服器內使用此指令")
            return
        
        if color == "NONE":
            await ctx.send("請輸入顏色代碼")
            return
        
        if len(color) != 6:
            await ctx.send("請輸入正確的顏色代碼")
            return
        
        current_roles = issued_guild.roles

        
        
        created_role = None
        
        if color not in [role.name for role in current_roles]:
            created_role = await issued_guild.create_role(name=color, color=discord.Color(int(color, 16)))
            
            await ctx.send(f"已新增顏色 {color}")
        else:
            created_role = [role for role in current_roles if role.name == color][0]
            await ctx.send("此顏色已存在")
        
        if created_role is None:
            await ctx.send("發生錯誤")
            return
        
            
        
        author = ctx.author
        author = cast(discord.Member, author)
        
        await author.add_roles(created_role)
        
        self.dbcursor.execute(f'INSERT INTO color (user_id, guild_id, color_hex) VALUES ({ctx.author.id}, {issued_guild.id}, "{color}")')
        self.dbconnect.commit()
        await ctx.send("已設定顏色")
        await created_role.edit(position=46)
    
    @commands.hybrid_command(name="清除顏色")
    @app_commands.guilds(utcs, hpsh)
    async def cleanup(self, ctx: commands.Context) -> None:
        issued_guild = ctx.guild if ctx.guild is not None else "ERROR"
        
        if issued_guild == "ERROR":
            await ctx.send("請在伺服器內使用此指令")
            return
        

        # current_user = self.color_json.get(str(ctx.author.id), None)
        
        set_color = self.dbcursor.execute(f'SELECT color_hex FROM color WHERE user_id = {ctx.author.id} AND guild_id = {issued_guild.id}').fetchone()[0]
        # await ctx.send(set_color)
        author = ctx.author
        author = cast(discord.Member, author)
        
        if set_color is not None:
            for roles in issued_guild.roles:
                if roles.name == set_color:
                    await author.remove_roles(roles)
                    
                    self.dbcursor.execute(f'DELETE FROM color WHERE user_id = {ctx.author.id} AND guild_id = {issued_guild.id}')
                    
                    if len(roles.members) == 0:
                        await roles.delete()
                    await ctx.send("已清除顏色")
                    return
        await ctx.send("你沒有顏色")
        # with open("cogs/asset/color.json", "w") as f:
        #     json.dump(self.color_json, f)
        
        
    @commands.hybrid_command(name="權限確認")
    @app_commands.guilds(utcs, hpsh)
    async def checkpermission(self, ctx: commands.Context, id) -> None:
        if ctx.guild is None:
            await ctx.send("請在伺服器內使用此指令")
            return
        k = await ctx.guild.fetch_roles()
        for i in k:
            if i.name == id:
                await ctx.send(f"權限確認: {i.position}")
                return

    
async def setup(bot: commands.Bot):
    await bot.add_cog(ColorChanger(bot))