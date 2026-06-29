# import requests
# from PIL import Image, ImageFile
# import io, os
# # https://stickershop.line-scdn.net/sticonshop/v1/sticon/6124aa4ae72c607c18108562/iPhone/039_animation.png

# real_sticker_png = requests.get("https://stickershop.line-scdn.net/sticonshop/v1/sticon/6124aa4ae72c607c18108562/iPhone/039_animation.png", stream=True)
# arr = io.BytesIO(real_sticker_png.content)
# arr.seek(0)

# ori_apng = Image.open(arr)
# ori_apng_arr = []

# for i in range(ori_apng.n_frames):
#     ori_apng.seek(i)
#     print(ori_apng.tell())
#     ori_apng_arr.append(ori_apng.copy())

# for png in ori_apng_arr:
#     png = png.convert("RGBA")

# # save all frames to gif
# ori_apng_arr[0].save("test.gif", save_all=True, append_images=ori_apng_arr[1:], loop=0)

# ori_apng = ori_apng.convert("RGBA")
# ori_apng.info.pop('transparent', None)
# print(ori_apng.info)
# output = io.BytesIO()
# ori_apng.save(output, format="GIF",save_all=True)
# ori_apng.save("test-{}.gif".format(2),save_all=True,disposal=2,loop=0)
# output_gif = open("test-{}.gif".format(2), "rb")

# file.filename = "file.gif"

# output_gif.close()
# os.remove("test-{}.gif".format(2))

# import requests
# import selenium
# from bs4 import BeautifulSoup
# from tqdm import tqdm
# import json
# import re
# import sqlite3
# from PIL import Image, ImageFile
# import io
# import os
# from enum import Enum
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service as ChromeService



# test_url = "https://mhwilds.kiranico.com/zh-Hant/data/items"
# response = requests.get(test_url)
# soup = BeautifulSoup(response.text, "html.parser")

# item_div = soup.select_one("body > div > div > div > div > div > div:nth-child(2) > div > div")
# if item_div is None:
#     exit()
    
# item_a = item_div.children

# for a in item_a:
#     print(a.text)



# testwebp = "https://api.hakush.in/zzz/UI/ExBigBoss001Big.webp"

# response = requests.get(testwebp)
# arr = io.BytesIO(response.content)
# arr.seek(0)

# image = Image.open(arr)
# # image = image.convert("RGBA")


# frames = []
# frame_width = 4096 // 16
# frame_height = 2048 // 8

# for y in range(8):
#     for x in range(16):
#         if y * 16 + x >= 120:  # Skip the last 8 frames
#             break
#         box = (x * frame_width, y * frame_height, (x + 1) * frame_width, (y + 1) * frame_height)
#         frame = image.crop(box)
#         frames.append(frame)
        
# frames[0].save("testwebp.webp", save_all=True, append_images=frames[1:], loop=0, duration=1000//30, lossless=True, exact=True, method=6)

# # Create directory if it doesn't exist
# os.makedirs("testwebp", exist_ok=True)

# # Save each frame to the directory
# for i, frame in enumerate(frames):
#     frame.save(f"testwebp/frame_{i}.png")


    
    
    
    





# armor = json.load(open("armor.json", "r"))

# db = sqlite3.connect("cogs/asset/mhwilds.db")
# c = db.cursor()

# c.execute("SELECT * FROM skill")
# skills = c.fetchall()

# for series in armor:
#     for armor_type in armor[series]:
#         if armor_type == "head" or armor_type == "body" or armor_type == "arm" or armor_type == "waist" or armor_type == "leg":
#             c.execute(
#                 "INSERT INTO armor (name, series_name, type, description, defense, fire_res, water_res, thunder_res, ice_res, dragon_res, slot1, slot2, slot3, icon_link_male, icon_link_female) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", 
#                 (armor[series][armor_type]["name"],
#                  armor[series][armor_type]["series_name"], 
#                  armor[series][armor_type]["type"], 
#                  armor[series][armor_type]["description"],
#                  armor[series][armor_type]["defense"],
#                  armor[series][armor_type]["fire"], 
#                  armor[series][armor_type]["water"],
#                  armor[series][armor_type]["thunder"],
#                  armor[series][armor_type]["ice"], 
#                  armor[series][armor_type]["dragon"],
#                  armor[series][armor_type]["slot1"], 
#                  armor[series][armor_type]["slot2"],
#                  armor[series][armor_type]["slot3"], 
#                  armor[series][armor_type]["icon_link_male"], 
#                  armor[series][armor_type]["icon_link_female"])
#                 )

# db.commit()

# armor_db = c.execute("SELECT * FROM armor").fetchall()

# print(armor_db)

# for series in armor:
#     for armor_type in armor[series]:
#         if armor_type == "head" or armor_type == "body" or armor_type == "arm" or armor_type == "waist" or armor_type == "leg":
#             for skill in armor[series][armor_type]["skill"]:
#                 armor_id = list(filter(lambda x: x[1] == armor[series][armor_type]["name"], armor_db))[0][0]
#                 skill_id = list(filter(lambda x, skill=skill: x[1] == skill["name"], skills))[0][0]
#                 print(armor_id, skill_id, skill["level"])
#                 c.execute("INSERT INTO armor_skills (armor_id, skill_id, level) VALUES (?,?,?)", (armor_id, skill_id, skill["level"]))

# db.commit()




# def create_empty_armor():
#     return {
#         "name": None,
#         "series_name": None,
#         "type": None,
#         "description": None,
#         "defense":None,
#         "fire": None,
#         "water": None,
#         "thunder": None, 
#         "ice": None,
#         "dragon": None,
#         "slot1": None,
#         "slot2": None,
#         "slot3": None,
#         "icon_link_male": None,
#         "icon_link_female": None,
#         "skill": []
#         }

# test_url = "https://mhwilds.kiranico.com/zh-Hant/data/armor-series"
# response = requests.get(test_url)
# soup = BeautifulSoup(response.text, "html.parser")

# tab = soup.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div > div > table")

# if tab is None:
#     exit()
    
# exclude_list = ["公會騎士","兵之甲冑","劍豪的獨眼","鬼角假髮","龍人族之耳"]

# table = tab.find_all("tr")

# # two row a group
# f = True
# armor = {}

# def return_skill_arr(tr):
#         skill_arr = []
#         skill_a = tr.find_all("td")[3].find_all("a")
#         for a in skill_a:
#             skill_text = a.text
#             splited = skill_text.split(" +")
#             skill_arr.append({
#                 "name": splited[0],
#                 "level": int(splited[1])
#             })
                
#         # print(skill_arr)
#         return skill_arr
    
# def get_slot(tr) -> tuple:
#     slot = tr.find_all("td")[2].text
#     matches = re.findall(r'\[(\d+)\]', slot)
    
#     return tuple(map(int, matches))

# def get_not_null_position(tr) -> list[int]:
#     td = tr.find_all("td")
#     not_null_position = []
    
#     for idx, data in enumerate(td):
#         if data.find("img") is not None:
#             not_null_position.append(idx-1)
#         # else:
#             # not_null_position.append(None)
    
#     return not_null_position

# for i in tqdm(range(0, len(table), 2)):
#     a = table[i].find("a")
#     if a.text in exclude_list:
#         continue
    
#     name = a.text
    
    
    
    
#     male_icons = table[i].find_all("td")
#     female_icons = table[i+1].find_all("td")
    
#     male_icon_links = []
#     female_icon_links = []
    
#     for idx, icon in enumerate(male_icons):
#         if idx == 0:
#             continue
        
        
#         if icon.find("img") is None:
#             male_icon_links.append(None)
#             continue
        
#         male_icon_links.append(icon.find("img")["src"])
    
#     # print(male_icon_links)
    
#     for idx, icon in enumerate(female_icons):
#         if idx == 0:
#             continue
        
#         if icon.find("img") is None:
#             female_icon_links.append(None)
#             continue
        
#         female_icon_links.append(icon.find("img")["src"])
        
        
#     inner_request = requests.get("https://mhwilds.kiranico.com" + a["href"])
#     inner_soup = BeautifulSoup(inner_request.text, "html.parser")
    
#     description_table = inner_soup.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div:nth-child(3) > div > table")
#     if description_table is None:
#         continue
    
#     defense_table = inner_soup.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div:nth-child(4) > div > table")
    
#     if defense_table is None:
#         continue
    
#     skill_table = inner_soup.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div:nth-child(5) > div > table")
    
#     if skill_table is None:
#         continue
    
#     armor[name] = {}
    
    
    
#     description_tr = description_table.find_all("tr")
#     defense_tr = defense_table.find_all("tr")
#     skill_tr = skill_table.find_all("tr")
    
#     pos = get_not_null_position(table[i])

#     if len(pos) != 5:
#         print("Find special armor, head into special routine, Pos: ", pos, "Name: ", name, "links: ", male_icon_links)
        
#         for idx, p in enumerate(pos):
            
#             description_tr = description_table.find_all("tr")
#             skill_tr = skill_table.find_all("tr")
            
#             armor_type = ""
            
#             if p == 0:
#                 armor_type = "head"
#             elif p == 1:
#                 armor_type = "body"
#             elif p == 2:
#                 armor_type = "arm"
#             elif p == 3:
#                 armor_type = "waist"
#             elif p == 4:
#                 armor_type = "leg"
                
#             armor[name][armor_type] = create_empty_armor()
#             armor[name][armor_type]["series_name"] = name
#             armor[name][armor_type]["name"] = description_tr[idx].find_all("td")[0].text
#             armor[name][armor_type]["type"] = p
#             armor[name][armor_type]["description"] = description_tr[idx].find_all("td")[1].text
#             armor[name][armor_type]["defense"] = int(defense_tr[idx+1].find_all("td")[2].text)
#             armor[name][armor_type]["fire"] = int(defense_tr[idx+1].find_all("td")[3].text)
#             armor[name][armor_type]["water"] = int(defense_tr[idx+1].find_all("td")[4].text)
#             armor[name][armor_type]["thunder"] = int(defense_tr[idx+1].find_all("td")[5].text)
#             armor[name][armor_type]["ice"] = int(defense_tr[idx+1].find_all("td")[6].text)
#             armor[name][armor_type]["dragon"] = int(defense_tr[idx+1].find_all("td")[7].text)
#             armor[name][armor_type]["skill"] = return_skill_arr(skill_tr[idx+1])
#             armor[name][armor_type]["slot1"], armor[name][armor_type]["slot2"], armor[name][armor_type]["slot3"] = get_slot(skill_tr[idx+1])
#             armor[name][armor_type]["icon_link_male"] = male_icon_links[p]
#             armor[name][armor_type]["icon_link_female"] = female_icon_links[p]
            
        

#         continue
    
    
#     armor[name]["head"] = create_empty_armor()
#     armor[name]["body"] = create_empty_armor()
#     armor[name]["arm"] = create_empty_armor()
#     armor[name]["waist"] = create_empty_armor()
#     armor[name]["leg"] = create_empty_armor()
           
    

#     armor[name]["head"]["series_name"] = name
#     armor[name]["body"]["series_name"] = name
#     armor[name]["arm"]["series_name"] = name
#     armor[name]["waist"]["series_name"] = name
#     armor[name]["leg"]["series_name"] = name
    
#     armor[name]["head"]["name"] = description_tr[0].find_all("td")[0].text
#     armor[name]["body"]["name"] = description_tr[1].find_all("td")[0].text
#     armor[name]["arm"]["name"] = description_tr[2].find_all("td")[0].text
#     armor[name]["waist"]["name"] = description_tr[3].find_all("td")[0].text
#     armor[name]["leg"]["name"] = description_tr[4].find_all("td")[0].text
    
#     armor[name]["head"]["type"] = 0
#     armor[name]["body"]["type"] = 1
#     armor[name]["arm"]["type"] = 2
#     armor[name]["waist"]["type"] = 3
#     armor[name]["leg"]["type"] = 4
    
#     armor[name]["head"]["description"] = description_tr[0].find_all("td")[1].text
#     armor[name]["body"]["description"] = description_tr[1].find_all("td")[1].text
#     armor[name]["arm"]["description"] = description_tr[2].find_all("td")[1].text
#     armor[name]["waist"]["description"] = description_tr[3].find_all("td")[1].text
#     armor[name]["leg"]["description"] = description_tr[4].find_all("td")[1].text
    
    
    
#     if len(defense_tr) != 6:
#         continue
    
#     armor[name]["head"]["defense"] = int(defense_tr[1].find_all("td")[2].text)
#     armor[name]["body"]["defense"] = int(defense_tr[2].find_all("td")[2].text)
#     armor[name]["arm"]["defense"] = int(defense_tr[3].find_all("td")[2].text)
#     armor[name]["waist"]["defense"] = int(defense_tr[4].find_all("td")[2].text)
#     armor[name]["leg"]["defense"] = int(defense_tr[5].find_all("td")[2].text)
    
#     armor[name]["head"]["fire"] = int(defense_tr[1].find_all("td")[3].text)
#     armor[name]["body"]["fire"] = int(defense_tr[2].find_all("td")[3].text)
#     armor[name]["arm"]["fire"] = int(defense_tr[3].find_all("td")[3].text)
#     armor[name]["waist"]["fire"] = int(defense_tr[4].find_all("td")[3].text)
#     armor[name]["leg"]["fire"] = int(defense_tr[5].find_all("td")[3].text)
    
#     armor[name]["head"]["water"] = int(defense_tr[1].find_all("td")[4].text)
#     armor[name]["body"]["water"] = int(defense_tr[2].find_all("td")[4].text)
#     armor[name]["arm"]["water"] = int(defense_tr[3].find_all("td")[4].text)
#     armor[name]["waist"]["water"] = int(defense_tr[4].find_all("td")[4].text)
#     armor[name]["leg"]["water"] = int(defense_tr[5].find_all("td")[4].text)
    
#     armor[name]["head"]["thunder"] = int(defense_tr[1].find_all("td")[5].text)
#     armor[name]["body"]["thunder"] = int(defense_tr[2].find_all("td")[5].text)
#     armor[name]["arm"]["thunder"] = int(defense_tr[3].find_all("td")[5].text)
#     armor[name]["waist"]["thunder"] = int(defense_tr[4].find_all("td")[5].text)
#     armor[name]["leg"]["thunder"] = int(defense_tr[5].find_all("td")[5].text)
    
#     armor[name]["head"]["ice"] = int(defense_tr[1].find_all("td")[6].text)
#     armor[name]["body"]["ice"] = int(defense_tr[2].find_all("td")[6].text)
#     armor[name]["arm"]["ice"] = int(defense_tr[3].find_all("td")[6].text)
#     armor[name]["waist"]["ice"] = int(defense_tr[4].find_all("td")[6].text)
#     armor[name]["leg"]["ice"] = int(defense_tr[5].find_all("td")[6].text)
    
#     armor[name]["head"]["dragon"] = int(defense_tr[1].find_all("td")[7].text)
#     armor[name]["body"]["dragon"] = int(defense_tr[2].find_all("td")[7].text)
#     armor[name]["arm"]["dragon"] = int(defense_tr[3].find_all("td")[7].text)
#     armor[name]["waist"]["dragon"] = int(defense_tr[4].find_all("td")[7].text)
#     armor[name]["leg"]["dragon"] = int(defense_tr[5].find_all("td")[7].text)
    
    
    
#     armor[name]["head"]["skill"] = return_skill_arr(skill_tr[1])
#     armor[name]["body"]["skill"] = return_skill_arr(skill_tr[2])
#     armor[name]["arm"]["skill"] = return_skill_arr(skill_tr[3])
#     armor[name]["waist"]["skill"] = return_skill_arr(skill_tr[4])
#     armor[name]["leg"]["skill"] = return_skill_arr(skill_tr[5])
        
#     armor[name]["head"]["slot1"], armor[name]["head"]["slot2"], armor[name]["head"]["slot3"] = get_slot(skill_tr[1])
#     armor[name]["body"]["slot1"], armor[name]["body"]["slot2"], armor[name]["body"]["slot3"] = get_slot(skill_tr[2])
#     armor[name]["arm"]["slot1"], armor[name]["arm"]["slot2"], armor[name]["arm"]["slot3"] = get_slot(skill_tr[3])
#     armor[name]["waist"]["slot1"], armor[name]["waist"]["slot2"], armor[name]["waist"]["slot3"] = get_slot(skill_tr[4])
#     armor[name]["leg"]["slot1"], armor[name]["leg"]["slot2"], armor[name]["leg"]["slot3"] = get_slot(skill_tr[5])
    
#     armor[name]["head"]["icon_link_male"] = male_icon_links[0]
#     armor[name]["body"]["icon_link_male"] = male_icon_links[1]
#     armor[name]["arm"]["icon_link_male"] = male_icon_links[2]
#     armor[name]["waist"]["icon_link_male"] = male_icon_links[3]
#     armor[name]["leg"]["icon_link_male"] = male_icon_links[4]
    
#     armor[name]["head"]["icon_link_female"] = female_icon_links[0]
#     armor[name]["body"]["icon_link_female"] = female_icon_links[1]
#     armor[name]["arm"]["icon_link_female"] = female_icon_links[2]
#     armor[name]["waist"]["icon_link_female"] = female_icon_links[3]
#     armor[name]["leg"]["icon_link_female"] = female_icon_links[4]
        

# with open("armor.json", "w", encoding="utf-8") as f:
#     f.write(json.dumps(armor, indent=4, ensure_ascii=False))


    
# a_arr = tab.find_all("a")
# for a in a_arr:
#     if a.text in exclude_list:
#         continue
    
    
    
#     print(a.text)
    # response = requests.get("https://mhwilds.kiranico.com" + a["href"])
    # s_a = BeautifulSoup(response.text, "html.parser")
    
    # armor_name = a.find("span").text
    # armor_type = s_a.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div:nth-child(3)




# deco = {}

# deco = json.load(open("deco.json", "r"))
# # print(deco)

# db = sqlite3.connect("cogs/asset/mhwilds.db")
# c = db.cursor()

# c.execute("SELECT * FROM skill")
# skill = c.fetchall()

# for i in deco:
#     # print(deco[i])
#     higher_level_skill = list(deco[i])[0]
#     try:
#         lower_level_skill = list(deco[i])[1]
#     except:
#         lower_level_skill = None

#     # print(higher_level_skill)
#     deco[i]["main_skill"] = {}
#     deco[i]["main_skill"]["name"] = higher_level_skill
#     deco[i]["main_skill"]["id"] = list(filter(lambda x: x[1] == higher_level_skill, skill))[0][0]
#     deco[i]["main_skill"]["level"] = deco[i][higher_level_skill]
#     deco[i].pop(higher_level_skill)
    
#     if lower_level_skill is not None:
#         deco[i]["sub_skill"] = {}
#         deco[i]["sub_skill"]["name"] = lower_level_skill
#         deco[i]["sub_skill"]["id"] = list(filter(lambda x: x[1] == lower_level_skill, skill))[0][0]
#         deco[i]["sub_skill"]["level"] = deco[i][lower_level_skill]
#         deco[i].pop(lower_level_skill)
#     else:
#         deco[i]["sub_skill"] = {}
#         deco[i]["sub_skill"]["name"] = None
#         deco[i]["sub_skill"]["id"] = None
#         deco[i]["sub_skill"]["level"] = None
    
    
#     match = re.search(r'【(\d+)】', i) 
#     if match:
#         deco[i]["slot"] = int(match.group(1))
#     else:
#         deco[i]["slot"] = 0
    
#     # print(deco[i])
    
    
# print(json.dumps(deco, indent=4, ensure_ascii=False))

# for i in deco:
#     c.execute("INSERT INTO decoration (name, main_skill_id, main_level, sub_skill_id, sub_level, slot) VALUES (?, ?, ?, ?, ?, ?)", (i, deco[i]["main_skill"]["id"], deco[i]["main_skill"]["level"], deco[i]["sub_skill"]["id"], deco[i]["sub_skill"]["level"], deco[i]["slot"]))

# db.commit()



# test_url = "https://mhwilds.kiranico.com/zh-Hant/data/decorations"
# response = requests.get(test_url)
# soup = BeautifulSoup(response.text, "html.parser")

# element = soup.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div > div")

# if element is None:
#     print("Not found")
#     exit()
    
# a = element.find_all("a")

# decoration = {}

# for i in a:
#     response = requests.get("https://mhwilds.kiranico.com" + i["href"])
#     s_a = BeautifulSoup(response.text, "html.parser")
    
#     decoration_name = i.find("span").text
    
#     e_a = s_a.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div:nth-child(3) > div")
    
#     if e_a is None:
#         print("Not found")
#         continue
    
#     skill = {}
    
#     e_a_a = e_a.find_all("tr")
#     for i in e_a_a:
#         # i.find("td:nth-child(1)")
#         skill_name_element = i.select_one("td:nth-child(1)").find("span").text
#         skill_level_element = int(i.select_one("td:nth-child(2)").find("span").text[2])
        
#         # print(skill_name_element, skill_level_element)
#         skill[skill_name_element] = skill_level_element
        
    
#     # print(decoration_name, skill)
#     decoration[decoration_name] = skill
    
# print(decoration)
        
        


# import sqlite3

# conn = sqlite3.connect("cogs/asset/mhwilds.db")

# c = conn.cursor()


# for i in a:
#     print(i["href"])
#     c.execute("INSERT INTO skill (name, url) VALUES (?, ?)", (i.text, i["href"]))

# conn.commit()

# c.execute("SELECT * FROM skill")
# print(c.fetchall())
# import re
# att_str = "{CAL:-65+100,1,2}"

# temp_match = re.match(r"{CAL:(-\d+)\+(\d+),(\d+),(\d+)}", att_str)
# print(temp_match.group(1))  # -1
# print(temp_match.group(2))  # 100
# print(temp_match.group(3))  # 0
# print(temp_match.group(4))  # 0


from typing import List


class Solution:
    def countDigitOne(self, n: int) -> int:
        num = 0
        for i in range(0, n + 1):
            test_str = str(i)
            for c in test_str:
                if c == '1':
                    num += 1

        return num
    
if __name__ == '__main__':
    s = Solution()
    print(s.countDigitOne(824883294))  # Output: 301