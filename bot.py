import datetime
from mimetypes import init
import os
import asyncio

from discord import Client
from discord import Guild
from discord.ext import commands
from discord import Intents
import discord


client = Client
guild = Guild
intents = Intents.default()
intents.message_content = True

   

# bot = commands.Bot(command_prefix="$", description='一隻艾路貓，會狠狠的戳人。',intents=intents)


class UTCSBot(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix="$", description='一隻艾路貓，會狠狠的戳人。',intents=intents)
        
    async def initialize_cog(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
    async def setup_hook(self):
        await self.initialize_cog()
        # await self.tree.sync(guild = discord.Object(id = 516470319242805264))
        

async def main():
    bot = UTCSBot()
    BOT_TOKEN = is_prod = os.environ.get('TOKEN', None)
    await bot.start(BOT_TOKEN)

asyncio.run(main())

# bot.run(BOT_TOKEN)
