from ctypes import Union
import discord
from discord.ext import commands
from discord import app_commands
from static import utcs, hpsh

class Slash(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        
    # @app_commands.command(name="testing")
    @commands.hybrid_command(name="testing_hybrid", with_app_command=True, description="?")
    @app_commands.guilds(utcs, hpsh)
    async def testing(self, ctx: commands.Context) -> None:
        await ctx.send("???")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(Slash(bot))
        
