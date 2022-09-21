from discord.ext import commands
from discord.ext.commands import Bot

class Base(commands.Cog):
    
    def __init__(self, bot:Bot):
        self.bot = bot


    @commands.command()
    async def load(self, ctx, extension):
        await self.bot.load_extension(f'cogs.{extension}')
        await ctx.send("已載入插件"+extension)


    @commands.command()
    async def unload(self, ctx, extension):
        await self.bot.unload_extension(f'cogs.{extension}')
        await ctx.send("已卸下插件"+extension)

    @commands.command()
    async def reload(self, ctx, extension):
        await self.bot.unload_extension(f'cogs.{extension}')
        await self.bot.load_extension(f'cogs.{extension}')
        await ctx.send("已重新載入插件"+extension)
        
async def setup(bot):
    await bot.add_cog(Base(bot))