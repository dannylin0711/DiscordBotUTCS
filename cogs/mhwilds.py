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
import copy
import sqlite3


class MHWilds(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.db = sqlite3.connect('cogs/asset/mhwilds.db')
        self.cursor = self.db.cursor()
        
    @commands.hybrid_command(name="武器資訊", description="查詢武器資訊")
    async def weapon_info(self, ctx: commands.Context, weapon_name: str):
        pass
        
        
    
async def setup(bot: commands.Bot):
    await bot.add_cog(MHWilds(bot))