import datetime
from mimetypes import init
import os
import asyncio
import sys
from discord import Client
from discord import Guild
from discord.ext import commands
from discord import Intents
import discord
import logging
import logging.handlers

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename='discord.log',
    encoding='utf-8',
    maxBytes=1 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

cogwatch_logger = logging.getLogger('cogwatch')
cogwatch_logger.setLevel(logging.DEBUG)
watch_handler = logging.StreamHandler(sys.stdout)
watch_handler.setFormatter(logging.Formatter('[%(name)s] %(message)s'))
cogwatch_logger.addHandler(watch_handler)

client = Client
guild = Guild
intents = Intents.all()
intents.message_content = True

   

# bot = commands.Bot(command_prefix="$", description='一隻艾路貓，會狠狠的戳人。',intents=intents)


class UTCSBot(commands.Bot):
    
    def __init__(self):
        super().__init__(
            command_prefix="$",
            description='一隻艾路貓，會狠狠的戳人。',
            intents=intents,
            allowed_contexts=discord.app_commands.AppCommandContext(
                guild=True,
                dm_channel=True,
                private_channel=True
            ),
            allowed_installs=discord.app_commands.AppInstallationType(
                guild=True,
                user=True
            ),
        )
        
    async def initialize_cog(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        
    async def setup_hook(self):
        await self.initialize_cog()
        await self.tree.sync()  # Sync commands globally
        # await self.tree.sync(guild = discord.Object(id = 516470319242805264))
        

async def main():
    bot = UTCSBot()
    BOT_TOKEN = is_prod = os.environ.get('TOKEN', None)
    await bot.start(BOT_TOKEN) # type: ignore

asyncio.run(main())

# bot.run(BOT_TOKEN)
