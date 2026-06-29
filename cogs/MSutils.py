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

base_url = "https://tw-event.beanfun.com/MapleStory/eventad/EventAD.aspx?EventADID={}"


source = {
    "golden_apple":8369,
    "fashion_box":8373,
    "star_pack":8370,
    "pet_box":8374,
    "magical_frame":8614,
    "monster_cardpack":8375,
    "magical_harp":8371,
    "monster_cube":8420,
    "star_force":8388,
}



class MSUtils(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.data = {}
        
        self.star_force_enum ={
            "success": "成功",
            "broke": "破壞",
            "failed_down": "降星",
            "failed_keep": "保持"
        }
        

    class ReCube(discord.ui.View):
        def __init__(self, data):
            super().__init__()
            self.data = data
            self.washed_times = 1

        @discord.ui.button(label="重洗", style=discord.ButtonStyle.primary)
        async def re_cube(self, interaction: discord.Interaction, button: discord.ui.Button):
            times = 3
            prize = self.data
            self.washed_times += 1
            prize_str = ""
            total = 0
            for item, prob in prize.items():
                real_num = float(prob[:-1])/100
                total += real_num
            
            prize_str += "目前花費：{0:>6}元\n\n".format(self.washed_times * 30)
            
            for _ in range(times):
                cumulative_prob = 0
                rand = random.random() * total
                for item, prob in prize.items():
                    real_num = float(prob[:-1])/100
                    cumulative_prob += real_num
                    # print(cumulative_prob, rand, item, prob, real_num)
                    if rand < cumulative_prob:
                        prize_str += item + " "
                        break
                prize_str += "\n"
                
                    
            await interaction.response.edit_message(view=self, content=prize_str)
            
    class MonsterCubeView(discord.ui.View):
        # title = "萌獸潛能自訂"
        # selection_1 = discord.ui.Select(placeholder="請選擇潛能")
        # selection_1_1 = discord.ui.Select(placeholder="請選擇潛能")
        # selection_2 = discord.ui.Select(placeholder="請選擇潛能")
        # selection_2_1 = discord.ui.Select(placeholder="請選擇潛能")
        # selection_3 = discord.ui.Select(placeholder="請選擇潛能")
        # selection_3_1 = discord.ui.Select(placeholder="請選擇潛能")
        
        def __init__(self, data:dict):
            super().__init__()
            self.data = data
            self.item_keys = data.keys()
            self.selection_1 = discord.ui.Select(placeholder="請選擇潛能")
            self.selection_2 = discord.ui.Select(placeholder="請選擇潛能")
            self.skill_int = 1
            
            self.selected = {}
            # self.selection_3 = discord.ui.Select(placeholder="請選擇潛能")
            
            
            for i, key in enumerate(self.item_keys):
                if i < 20:
                    self.selection_1.add_option(label=key, value=str(i))
                elif i < 40:
                
                    self.selection_2.add_option(label=key, value=str(i))
                # self.selection_3.add_option(label=key, value=str(i))
            
            self.selection_1.callback = self.on_select
            self.selection_2.callback = self.on_select
            # self.selection_3.callback = self.on_select
            
            self.add_item(self.selection_1)
            self.add_item(self.selection_2)
            
            self.開洗 = discord.ui.Button(label="開洗", style=discord.ButtonStyle.primary)
            self.開洗.callback = self.on_washing
            self.add_item(self.開洗)
            # self.add_item(self.selection_3)
                
        @discord.ui.button(label="選擇第一潛能", style=discord.ButtonStyle.primary)
        async def on_submit_1(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            self.skill_int = 1
            
            t = "現在選擇第一潛能 \n目前潛能:\n" + interaction.message.content
            await interaction.response.edit_message(view=self, content=t)
        @discord.ui.button(label="選擇第二潛能", style=discord.ButtonStyle.primary)
        async def on_submit_2(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            self.skill_int = 2
            t = "現在選擇第二潛能 \n目前潛能:\n" + interaction.message.content
            await interaction.response.edit_message(view=self, content=t)
        @discord.ui.button(label="選擇第三潛能", style=discord.ButtonStyle.primary)
        async def on_submit_3(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            self.skill_int = 3
            t = "現在選擇第三潛能 \n目前潛能:\n" + interaction.message.content
            await interaction.response.edit_message(view=self, content=t)
            
        async def on_select(self, interaction: discord.Interaction) -> None:
            temp = ""
            if len(self.selection_1.values) == 1:
                temp = self.selection_1.values[0]
            elif len(self.selection_2.values) == 1:
                temp = self.selection_2.values[0]
            # print(int(temp))
            try:
                if self.skill_int == 1:
                    self.selected["第一潛能"] = list(self.item_keys)[int(temp)]
                elif self.skill_int == 2:
                    self.selected["第二潛能"] = list(self.item_keys)[int(temp)]
                elif self.skill_int == 3:
                    self.selected["第三潛能"] = list(self.item_keys)[int(temp)]
            except ValueError:
                print("????")
                
            self.selection_1.values.clear()
            self.selection_2.values.clear()
            
            out = ""
            for key, item in self.selected.items():
                out += f"{key}: {item}\n"
            
            await interaction.response.edit_message(view=self, content=out)
            
        async def on_washing(self, interaction: discord.Interaction) -> None:
            c_origin = interaction.message.content
            await interaction.response.edit_message(content=c_origin+"\n正在洗...")
            times = 1
            prize = self.data
            # prize_str += "目前花費：{0:>6}元\n\n".format(30)
            total = 0
            for item, prob in prize.items():
                real_num = float(prob[:-1])/100
                total += real_num
            tm = 0
            while True:
                # t = ["最終傷害", "最終傷害", "最終傷害"]
                # t = ["最終傷害:+20", "最終傷害:+20", "魔法攻擊力%:+14"]
                t = []
                for _ in range(3):
                    cumulative_prob = 0
                    rand = random.random() * total
                    for item, prob in prize.items():
                        real_num = float(prob[:-1])/100
                        cumulative_prob += real_num
                        # print(cumulative_prob, rand, item, prob, real_num)
                        if rand < cumulative_prob:
                            t.append(item)
                            break
                flag = False
                count = {}
                
                for i in t:
                    if i in count:
                        count[i] += 1
                    else:
                        count[i] = 1
                        
                for p in prize.keys():
                    if p not in count:
                        count[p] = 0
                
                # print(count)
                
                wanted = {}
                if "第一潛能" in self.selected:
                    if self.selected["第一潛能"] not in wanted:
                        wanted[self.selected["第一潛能"]] = 1
                    else:
                        wanted[self.selected["第一潛能"]] += 1
                
                if "第二潛能" in self.selected:   
                    if self.selected["第二潛能"] not in wanted:
                        wanted[self.selected["第二潛能"]] = 1
                    else:
                        wanted[self.selected["第二潛能"]] += 1
                
                if "第三潛能" in self.selected:
                    if self.selected["第三潛能"] not in wanted:
                        wanted[self.selected["第三潛能"]] = 1
                    else:
                        wanted[self.selected["第三潛能"]] += 1
                    
                for wanted_key, wanted_item in wanted.items():
                    if wanted_item != count[wanted_key]:
                        flag = True
                        break
                
                if flag:
                    times += 1
                else:
                    break
                
            # mode_str = ""
            
            # if mode == 1:
            #     mode_str = "三終"
            # elif mode == 2:
            #     mode_str = "雙終魔"
            # elif mode == 3:
            #     mode_str = "雙終物"
            
            # c = c_origin + "\n洗到目標潛能花費：{0:>6}元\n\n".format(times*30)
            result = "結果：\n"
            for re in t:
                result += re + "\n"
            result += "\n"
            result += "洗到目標潛能花費：{0:>6}元\n\n".format(times*30)
            
            await interaction.followup.send(result)
            # await interaction.response.edit_message(view=self,content=c)
            
            
            
            
            # out = ""
            # for key, item in self.selected.items():
            #     out += f"{key}: {item}\n"
            # await interaction.response.edit_message(view=self, content=out + "\n我醒了會繼續弄，我睡一下")


    @commands.hybrid_command(name="抽", description="")
    @app_commands.guilds(utcs, hpsh)
    @app_commands.rename(selection="抽啥")
    @app_commands.rename(lottery_t="次數")
    @app_commands.choices(selection=[
        app_commands.Choice(name="黃金蘋果", value=1),
        app_commands.Choice(name="時尚隨機箱", value=2),
        # app_commands.Choice(name="星光錦囊", value=3),
        app_commands.Choice(name="寵物隨機箱", value=4),
        app_commands.Choice(name="魔法畫框", value=5),
        app_commands.Choice(name="萌獸卡牌包", value=6),
        app_commands.Choice(name="魔法豎琴", value=7),
    ])
    async def lottery(self, ctx: commands.Context, selection:int, lottery_t:int = 1) -> None:
        # if selection > 2:
        #     await ctx.send("還在弄")
        #     return
        
        # Randomly select a prize by the given probability
        times = 1
        prize = {}
        try:
            if selection == 1:
                prize = self.data["golden_apple"]["default"]
            elif selection == 2:
                prize = self.data["fashion_box"]["default"]
            elif selection == 5:
                prize = self.data["magical_frame"]["default"]
            elif selection == 6:
                prize = self.data["monster_cardpack"]["default"]
                times = 3
        except KeyError:
            await ctx.send("請先更新獎池")
            return
            
        if len(prize) == 0:
            await ctx.send("還在弄")
            return
        
        prize_str = ""
        total = 0
        for item, prob in prize.items():
            real_num = float(prob[:-1])/100
            total += real_num
        
        for k in range(lottery_t):
            prize_str += "{0:>4}:\n".format(k+1)
            for _ in range(times):
                cumulative_prob = 0
                rand = random.random() * total
                for item, prob in prize.items():
                    real_num = float(prob[:-1])/100
                    cumulative_prob += real_num
                    # print(cumulative_prob, rand, item, prob, real_num)
                    if rand < cumulative_prob:
                        prize_str += item + " "
                        break
                prize_str += "\n"
                
            if (k+1)%30 == 0:
                await ctx.send(prize_str)
                prize_str = "" 
                
        await ctx.send(prize_str)
        
    @commands.hybrid_command(name="洗", description="")
    @app_commands.guilds(utcs, hpsh)
    @app_commands.rename(selection="洗啥")
    @app_commands.choices(selection=[
        app_commands.Choice(name="萌獸方塊", value=1),
        app_commands.Choice(name="附加方塊", value=2),
    ])
    async def washing(self, ctx: commands.Context, selection:int) -> None:
        times = 1
        prize = {}
        try:
            if selection == 1:
                prize = self.data["monster_cube"]["default"]
                times = 3
            elif selection == 2:
                pass
            elif selection == 6:
                pass
        except KeyError:
            await ctx.send("請先更新獎池")
            return
            
        if len(prize) == 0:
            await ctx.send("還在弄")
            return
        
        prize_str = ""
        total = 0
        for item, prob in prize.items():
            real_num = float(prob[:-1])/100
            total += real_num

        if selection == 1:
            prize_str += "目前花費：{0:>6}元\n\n".format(30)
        
        
        for _ in range(times):
            cumulative_prob = 0
            rand = random.random() * total
            for item, prob in prize.items():
                real_num = float(prob[:-1])/100
                cumulative_prob += real_num
                # print(cumulative_prob, rand, item, prob, real_num)
                if rand < cumulative_prob:
                    prize_str += item + " "
                    break
            prize_str += "\n"
        await ctx.send(prize_str, view=self.ReCube(prize))

    @commands.hybrid_command(name="萌獸方塊水溝模式", description="")
    @app_commands.rename(mode="洗啥")
    @app_commands.choices(mode=[
        app_commands.Choice(name="自選", value=0),
        app_commands.Choice(name="三終", value=1),
        app_commands.Choice(name="雙終魔", value=2),
        app_commands.Choice(name="雙終物", value=3),
    ])
    async def washing_monstercube_with_condition(self, ctx: commands.Context, mode:int) -> None: 
        await ctx.defer()
        
        try:
            prize = self.data["monster_cube"]["default"]
        except KeyError:
            await ctx.send("請先更新獎池")
            return
        
        if mode == 0:
            v = self.MonsterCubeView(prize)
            if ctx.interaction is not None:
                await ctx.send("請選擇潛能", view=v)
                return
                
        
        times = 1

        # prize_str += "目前花費：{0:>6}元\n\n".format(30)
        total = 0
        for item, prob in prize.items():
            real_num = float(prob[:-1])/100
            total += real_num
        tm = 0
        while True:
            # t = ["最終傷害", "最終傷害", "最終傷害"]
            # t = ["最終傷害:+20", "最終傷害:+20", "魔法攻擊力%:+14"]
            t = []
            for _ in range(3):
                cumulative_prob = 0
                rand = random.random() * total
                for item, prob in prize.items():
                    real_num = float(prob[:-1])/100
                    cumulative_prob += real_num
                    # print(cumulative_prob, rand, item, prob, real_num)
                    if rand < cumulative_prob:
                        t.append(item)
                        break
            flag = False
            count = {}
            
            for i in t:
                if i in count:
                    count[i] += 1
                else:
                    count[i] = 1
            
            # print(count)
            if mode == 1:
                if "最終傷害:+20" not in count:
                    flag = True
                elif count["最終傷害:+20"] != 3:
                    flag = True
            elif mode == 2:
                if "魔法攻擊力%:+14" not in count or "最終傷害:+20" not in count:
                    flag = True
                elif count["最終傷害:+20"] != 2 or count["魔法攻擊力%:+14"] != 1:
                    flag = True
                    # print("????")
            elif mode == 3:
                if "物理攻擊力%:+14" not in count or "最終傷害:+20" not in count:
                    flag = True
                elif count["最終傷害:+20"] != 2 or count["物理攻擊力%:+14"] != 1:
                    flag = True
            
            if flag:
                times += 1
            else:
                break
            
        mode_str = ""
        
        if mode == 1:
            mode_str = "三終"
        elif mode == 2:
            mode_str = "雙終魔"
        elif mode == 3:
            mode_str = "雙終物"
            
        await ctx.send("洗到{0}花費：{1:>6}元\n\n".format(mode_str, times*30))
        
        
    
    
        
    @commands.hybrid_command(name="星力強化", description="")   
    @app_commands.rename(default_star="原始星力")
    @app_commands.rename(protect="保護")
    async def star_force(self, ctx: commands.Context, default_star: int = 0, protect: bool = True) -> None:
        if default_star < 0 or default_star > 24:
            await ctx.send("請輸入正確星力")
            return
        
        await ctx.defer()
        try:
            data = copy.deepcopy(self.data["star_force"]["default"])
        except KeyError:
            await ctx.send("請先更新獎池")
            return
        
        if len(data) == 0:
            await ctx.send("還在弄")
            return
        
        result_str = ""
        current_star = default_star
        # if on protect, item won't be destroyed
        # so the probability from destroyed item will be added to either failed_down or failed_keep
        if protect:
            for key, item in data.items():
                # item["failed_down"] = str(float(item["failed_down"][:-1]) + float(item["broke"][:-1])) + "%"
                # item["broke"] = "0%"
                if item["failed_down"] == "0.00%":
                    item["failed_keep"] = str(float(item["failed_keep"][:-1]) + float(item["broke"][:-1])) + "%"
                    item["broke"] = "0.00%"

                if item["failed_keep"] == "0.00%":
                    item["failed_down"] = str(float(item["failed_down"][:-1]) + float(item["broke"][:-1])) + "%"
                    item["broke"] = "0.00%"
                    
            current_star_data = data[default_star]
            # cumulative probability
            total = 0
            for key, item in current_star_data.items():
                print(item)
                total += float(item[:-1])/100
            print(total)
            rand = random.random() * total
            cumulative_prob = 0
            print(rand)
            for key, item in current_star_data.items():
                cumulative_prob += float(item[:-1])/100
                if rand < cumulative_prob:
                    result_str += self.star_force_enum[key] + "\n"
                    if key == "success":
                        current_star += 1
                    elif key == "failed_down":
                        current_star -= 1
                    break
        else:
            current_star_data = data[default_star]
            # cumulative probability
            total = 0
            for key, item in current_star_data.items():
                total += float(item[:-1])/100
            # print(total)
            rand = random.random() * total
            cumulative_prob = 0
            for key, item in current_star_data.items():
                cumulative_prob += float(item[:-1])/100
                if rand < cumulative_prob:
                    result_str += self.star_force_enum[key] + "\n"
                    if "success" in key:
                        current_star += 1
                    elif "broke" in key:
                        result_str += "你只剩他的靈魂還在了"
                    elif "failed_down" in key:
                        current_star -= 1

                    break
                
        result_str += "現在為 {} 星".format(current_star)
        
        await ctx.send(result_str, view=self.ReStarForceView(data, current_star, protect, self.star_force_enum))
            
                    
    class ReStarForceView(discord.ui.View):
        def __init__(self, data, star, protect, enum):
            super().__init__()
            self.data = data
            self.washed_times = 1
            self.star = star
            self.protect = protect
            self.star_force_enum = enum
            
            

        @discord.ui.button(label="強化", style=discord.ButtonStyle.primary)
        async def re_star_force(self, interaction: discord.Interaction, button: discord.ui.Button):
            times = 1
            data = self.data
            
            star_force_enum = self.star_force_enum
            protect = self.protect
            
            if self.star < 0 or self.star > 24:
                await interaction.response.edit_message(view=self, content="請輸入正確星力")
                return
            
            # await ctx.defer()
            # try:
            #     data = copy.deepcopy(self.data["star_force"]["default"])
            # except KeyError:
            #     await ctx.send("請先更新獎池")
            #     return
            
            # if len(data) == 0:
            #     await ctx.send("還在弄")
            #     return
            
            result_str = ""

            # if on protect, item won't be destroyed
            # so the probability from destroyed item will be added to either failed_down or failed_keep
            if protect:
                for key, item in data.items():
                    # item["failed_down"] = str(float(item["failed_down"][:-1]) + float(item["broke"][:-1])) + "%"
                    # item["broke"] = "0%"
                    if item["failed_down"] == "0.00%":
                        item["failed_keep"] = str(float(item["failed_keep"][:-1]) + float(item["broke"][:-1])) + "%"
                        item["broke"] = "0.00%"

                    if item["failed_keep"] == "0.00%":
                        item["failed_down"] = str(float(item["failed_down"][:-1]) + float(item["broke"][:-1])) + "%"
                        item["broke"] = "0.00%"
                        
                current_star_data = data[self.star]
                # cumulative probability
                total = 0
                for key, item in current_star_data.items():
                    print(item)
                    total += float(item[:-1])/100
                print(total)
                rand = random.random() * total
                cumulative_prob = 0
                print(rand)
                for key, item in current_star_data.items():
                    cumulative_prob += float(item[:-1])/100
                    if rand < cumulative_prob:
                        result_str += self.star_force_enum[key] + "\n"
                        if key == "success":
                            self.star += 1
                        elif key == "failed_down":
                            self.star -= 1
                        break
            else:
                current_star_data = data[self.star]
                # cumulative probability
                total = 0
                for key, item in current_star_data.items():
                    total += float(item[:-1])/100
                # print(total)
                rand = random.random() * total
                cumulative_prob = 0
                for key, item in current_star_data.items():
                    cumulative_prob += float(item[:-1])/100
                    if rand < cumulative_prob:
                        result_str += self.star_force_enum[key] + "\n"
                        if "success" in key:
                            self.star += 1
                        elif "broke" in key:
                            result_str += "你只剩他的靈魂還在了"
                        elif "failed_down" in key:
                            self.star -= 1

                        break
                    
            result_str += "現在為 {} 星".format(self.star)
                    
                    
            await interaction.response.edit_message(view=self, content=result_str)
        
        
        

    @commands.hybrid_command(name="更新獎池", description="")
    @app_commands.guilds(utcs, hpsh)
    async def updatelottery(self, ctx: commands.Context) -> None:
        await ctx.defer()
        for key, url in source.items():
            u = base_url.format(url)
            cmd = "curl -s --location --request GET '{}'".format(u)
            k = os.popen(cmd)
            response = k.read()

            soup = BeautifulSoup(response, 'html.parser')
            probability_tables = soup.find_all('table')
            
            data = {}

            if "golden_apple" in key:
                
                data["default"] = {}
                
                probability_table_default = probability_tables[0]
                for row in probability_table_default.find_all('tr'):
                    col = row.find_all('td')
                    if "道具名稱" in col[0].text:
                        continue
                    
                    if len(col) == 2:
                        data["default"][col[0].text.strip()] = col[1].text.strip()
                
                data["silver"] = {}
                data["gold"] = {}
                probability_table_silver = probability_tables[2]
                
                c = "silver"
                for row in probability_table_silver.find_all('tr'):
                    col = row.find_all('td')
                    if "道具名稱" in col[0].text or "幸運的銀色箱子" in col[0].text:
                        continue
                    if "幸運的金色箱子" in col[0].text:
                        c = "gold"
                        continue
                    if len(col) == 2:
                        data[c][col[0].text.strip()] = col[1].text.strip()

            elif "fashion_box" in key:
                
                data["default"] = {}
                probability_table_default = probability_tables[0]
                
                for idx, row in enumerate(probability_table_default.find_all('tr')):
                    col = row.find_all('td')
                    if "道具名稱" in col[0].text:
                        continue
                    
                    if len(col) == 2:
                        data["default"][col[0].text.strip()] = col[1].text.strip()
                        
                    if len(col) == 1:
                        data["default"][col[0].text.strip()] = probability_table_default.find_all('tr')[idx-1].find_all('td')[1].text.strip()

            elif "star_pack" in key:
                pass
            elif "pet_box" in key:
                data["default"] = {}
                probability_table_default = probability_tables[0]
                
                for idx, row in enumerate(probability_table_default.find_all('tr')):
                    col = row.find_all('td')
                    if "道具名稱" in col[0].text:
                        continue
                    
                    if len(col) == 2:
                        data["default"][col[0].text.strip()] = col[1].text.strip()
                
            elif "magical_frame" in key:
                data["default"] = {}
                probability_table_default = probability_tables[0]
                
                for idx, row in enumerate(probability_table_default.find_all('tr')):
                    col = row.find_all('td')
                    if "道具名稱" in col[0].text:
                        continue
                    
                    if len(col) == 2:
                        data["default"][col[0].text.strip()] = col[1].text.strip()
        
            elif "monster_cardpack" in key:
                data["default"] = {}
                probability_table_default = probability_tables[0]
                
                for idx, row in enumerate(probability_table_default.find_all('tr')):
                    col = row.find_all('td')
                    if "道具名稱" in col[0].text:
                        continue
                    
                    if len(col) == 2:
                        data["default"][col[0].text.strip()] = col[1].text.strip()

            elif "magical_harp" in key:
                data["default"] = {}
                probability_table_default = probability_tables[0]
                
                for idx, row in enumerate(probability_table_default.find_all('tr')):
                    col = row.find_all('td')
                    if "道具名稱" in col[0].text:
                        continue
                    
                    if len(col) == 2:
                        data["default"][col[0].text.strip()] = col[1].text.strip()
            elif "monster_cube" in key:
                data["default"] = {}
                probability_table_default = probability_tables[0]
                
                flag = True
                for idx, row in enumerate(probability_table_default.find_all('tr')):
                    col = row.find_all('td')
                    if "傳說" in col[0].text:
                        flag = False
                    if flag or "屬性" in col[0].text:
                        continue
                    
                    if len(col) == 7:
                        real_text = "{}:+{}".format(col[0].text.strip(), col[5].text.strip())
  
                        data["default"][real_text] = col[6].text.strip()
            elif "star_force" in key:
                data["default"] = {}
                probability_table_default = probability_tables[0]
                
                for idx, row in enumerate(probability_table_default.find_all('tr')):
                    col = row.find_all('td')
                    if idx == 0 or idx == 1:
                        continue
                    
                    if len(col) == 5:
                        print(col[1].text)
                        data["default"][idx - 2] = {}
                        data["default"][idx - 2]["success"] = col[1].text.strip()
                        data["default"][idx - 2]["broke"] = col[2].text.strip()
                        data["default"][idx - 2]["failed_down"] = col[3].text.strip()
                        data["default"][idx - 2]["failed_keep"] = col[4].text.strip()
                        
                print(json.dumps(data["default"], indent=2))
            
            self.data[key] = data
            
        
        # print(json.dumps(self.data, indent=4, ensure_ascii=False))
        await ctx.send("更新完畢")


    
async def setup(bot: commands.Bot):
    await bot.add_cog(MSUtils(bot))