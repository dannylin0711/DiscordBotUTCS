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

class RSSfeeder(commands.Cog):

    def __init__(self, bot):
        self.bot = bot




def setup(bot):
    bot.add_cog(RSSfeeder(bot))
