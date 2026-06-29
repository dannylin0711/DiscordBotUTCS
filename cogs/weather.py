import json
import multiprocessing
import pathlib
import socket
import time
from static import utcs, hpsh
from typing import List, Literal
import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import discord
from discord.ext import commands, tasks
from discord import app_commands, ForumChannel
import os
import random
from apscheduler.schedulers.background import BackgroundScheduler

# API token CWA-EC45FB49-CFD4-4DDA-B42D-7A380256F0E6

weather = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization=CWA-EC45FB49-CFD4-4DDA-B42D-7A380256F0E6&downloadType=WEB&format=JSON"

class Weather(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.json_data = None
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.get_weather, 'cron', hour=21, timezone='Asia/Taipei')
        self.scheduler.start()
        
        self.get_weather()
        
    def cog_unload(self):
        self.scheduler.shutdown()
        
        
    # auto update weather everyday at 21:00 using APScheduler
    def get_weather(self):
        response = requests.get(weather, verify=False)
        self.json_data = response.json()
        
    @commands.hybrid_command(name="天氣")
    @app_commands.guilds(utcs, hpsh)
    async def weather(self, ctx: commands.Context) -> None:
        # seperate the data to 1000 characters
        data = self.json_data
        # print(data)
        if data is None:
            await ctx.send("資料尚未更新")
            return
        
        selection = discord.ui.Select(placeholder="請選擇縣市", min_values=1, max_values=1)
        for loc in data["cwaopendata"]["dataset"]["location"]:
            selection.add_option(label=loc["locationName"], value=loc["locationName"])
            
        async def selection_callback(interaction: discord.Interaction):
            loc = interaction.data["values"][0]
            
            filtered_data = list(filter(lambda x: x["locationName"] == loc, data["cwaopendata"]["dataset"]["location"]))[0]
            weather_data = filtered_data["weatherElement"]
            weather_str = ""
            
            grouped_data = {}
            for element in weather_data:
                element_name = element["elementName"]
                for time_data in element["time"]:
                    start_time = time_data["startTime"]
                    end_time = time_data["endTime"]
                    
                    start_time = time.strftime("%Y-%m-%d %I:%M %p", time.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z"))
                    end_time = time.strftime("%Y-%m-%d %I:%M %p", time.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z"))
                    parameter_name = time_data["parameter"]["parameterName"]
                    time_key = f"{start_time} - {end_time}"
                    
                    if time_key not in grouped_data:
                        grouped_data[time_key] = {}
                    
                    if element_name == "Wx":
                        grouped_data[time_key]["天氣現象"] = parameter_name
                    elif element_name == "MaxT":
                        grouped_data[time_key]["最高溫度"] = f"{parameter_name}°C"
                    elif element_name == "MinT":
                        grouped_data[time_key]["最低溫度"] = f"{parameter_name}°C"
                    elif element_name == "CI":
                        grouped_data[time_key]["舒適度"] = parameter_name
                    elif element_name == "PoP":
                        grouped_data[time_key]["降雨機率"] = f"{parameter_name}%"
            
            # embed = discord.Embed(title=f"{loc} 天氣預報", color=discord.Color.blue())
            
            # for time_key, elements in grouped_data.items():
            #     embed.add_field(name="時間", value=time_key, inline=False)
            #     for element_name, value in elements.items():
            #         embed.add_field(name=element_name, value=value, inline=True)
            
            embed_arr = []
            
            weather_component = discord.ui.LayoutView()
            
            weather_section = discord.ui.Container()
            time_text = f"# {loc} 天氣預報\n"
            weather_section.add_item(discord.ui.TextDisplay(time_text))
            for time_key, elements in grouped_data.items():
                time_text = f"### {time_key}\n"
                
                for element_name, value in elements.items():
                    time_text += f"- **{element_name}**: {value}\n"
                
                
                time_text_display = discord.ui.TextDisplay(time_text)
                weather_section.add_item(time_text_display)
                # embed = discord.Embed(title=f"{loc} 天氣預報", color=discord.Color.blue())
                # embed.add_field(name="時間", value=time_key, inline=False)
                # for element_name, value in elements.items():
                #     embed.add_field(name=element_name, value=value, inline=True)
                # embed_arr.append(embed)
            
            weather_component.add_item(weather_section)
                
            await interaction.response.send_message(view=weather_component)
            # await interaction.response.send_message(embed=embed_arr[0])
            # await interaction.followup.send(embed=embed_arr[1])
            # await interaction.followup.send(embed=embed_arr[2])
            
            # await interaction.response.send_message(f"你選擇了{interaction.data['values'][0]}", ephemeral=True)
        
        selection.callback = selection_callback    
        
        view = discord.ui.View()
        view.add_item(selection)
        await ctx.send("請選擇縣市", view=view)
        # for i in range(0, len(data), 1000):
        #     await ctx.send(data[i:i+1000])
        
    
        
    
    
async def setup(bot: commands.Bot):
    await bot.add_cog(Weather(bot))