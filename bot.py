import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="$", description='A bot that greets the user back.')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
async def add(ctx, a: int, b: int):
    await ctx.send(a+b)

bot.login("NjI2NjA1NjQxMDkxNTE0Mzc4.XYwxlg.Q-6QtW7Q9Ipq9AJ5-iwWnKtaS9o")
bot.run('NjI2NjA1NjQxMDkxNTE0Mzc4.XYwxlg.Q-6QtW7Q9Ipq9AJ5-iwWnKtaS9o')