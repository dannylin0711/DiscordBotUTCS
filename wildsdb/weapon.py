import requests
import selenium
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import re
import sqlite3
from PIL import Image, ImageFile
import io
import os
from enum import Enum
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService

def parse_slot(span_input) -> tuple:
    span_input = span_input.select_one("span").find_all("span")
    slot = [0, 0, 0]
    
    for idx, span in enumerate(span_input):
        if span.text == "ー":
            slot[idx] = 0
        elif span.text == "①":
            slot[idx] = 1
        elif span.text == "②":
            slot[idx] = 2
        elif span.text == "③":
            slot[idx] = 3
            
    return tuple(slot)

def get_element(img_url) -> str:
    if matching := re.search(r"ElementType(\d+)\.png", img_url):
        element_index = int(matching.group(1))
        if element_index == 0:
            return "無"
        elif element_index == 1:
            return "火"
        elif element_index == 2:
            return "水"
        elif element_index == 3:
            return "雷"
        elif element_index == 4:
            return "冰"
        elif element_index == 5:
            return "龍"
        elif element_index == 6:
            return "毒"
        elif element_index == 7:
            return "睡眠"
        elif element_index == 8:
            return "麻痺"
        elif element_index == 9:
            return "爆破"
    return ""

def get_affinity(affinity_div) -> int:
    affinity_str = affinity_div.find_all("div")[0].text
    
    affinity_str = affinity_str.replace("%", "")
    if affinity_str == "":
        return 0
    else:
        return int(affinity_str)
    
    
def get_sharpness(sharpness_svg) -> str:
    sharpness_rects = sharpness_svg.find_all("rect")
    
    sharpness = []
    
    for rect in sharpness_rects:
        if rect["fill"] == "#141414":
            continue
        sharpness.append(rect["width"])
    
    sharpness = ",".join(sharpness)
    # print(sharpness)
    return sharpness
    
    
    
    

class WeaponIndex(Enum):
    GreatSword = "LONG_SWORD"
    SwordAndShield = "SHORT_SWORD"
    DualBlades = "TWIN_SWORD"
    LongSword = "TACHI"
    Hammer = "HAMMER"
    HuntingHorn = "WHISTLE"
    Lance = "LANCE"
    Gunlance = "GUN_LANCE"
    SwitchAxe = "SLASH_AXE"
    ChargeBlade = "CHARGE_AXE"
    InsectGlaive = "ROD"
    Bow = "BOW"
    HeavyBowgun = "HEAVY_BOWGUN"
    LightBowgun = "LIGHT_BOWGUN"
    


options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-extensions")
options.binary_location = "/usr/bin/chromium-browser"

driver_path = ChromeService("/usr/bin/chromedriver")
driver_path.start()

test_url = "https://mhwilds.kiranico.com/zh-Hant/data/weapons"
driver = webdriver.Chrome(options=options, service=driver_path)
driver.get(test_url)

db = sqlite3.connect("../cogs/asset/mhwilds.db")
c = db.cursor()

skills = c.execute("SELECT * FROM skill").fetchall()
items = c.execute("SELECT * FROM item").fetchall()

weapons = {}

from selenium.webdriver.common.by import By
for weapon in WeaponIndex:
    # print(weapon.name)
    driver.find_element(by=By.CSS_SELECTOR, value=f"#radix-\:Rfqfnnnkkq\:-trigger-{weapon.value}").click()
    driver.implicitly_wait(0.5)
    r = driver.page_source
    soup = BeautifulSoup(r, "html.parser")
    weapon_table = soup.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div > div")
    weapons[weapon.name] = []
    if weapon_table is None:
        exit()
        
    c = weapon_table.select_one(f"#radix-\:Rfqfnnnkkq\:-content-{weapon.value}")
    if c is None:
        print(f"Can't find {weapon.name}")
        continue
    
    
    weapon_table_inner = c.select_one("table")
    if weapon_table_inner is None:
        print(f"Can't find {weapon.name}")
        continue
    
    weapon_table_inner_tr = weapon_table_inner.find_all("tr")
    
    for tr in tqdm(weapon_table_inner_tr, total=len(weapon_table_inner_tr), desc=weapon.name):
        
        
        weapon_inner = {}
        
        weapon_inner["name"] = tr.find_all("td")[1].text
        weapon_inner["type"] = weapon.name
        weapon_inner["slot1"], weapon_inner["slot2"], weapon_inner["slot3"] = parse_slot(tr.find_all("td")[2])
        weapon_inner["attack"] = int(tr.find_all("td")[3].text)
        weapon_inner["affinity"] = get_affinity(tr.find_all("td")[5])
        
                
        if weapon == WeaponIndex.Gunlance or weapon == WeaponIndex.ChargeBlade or weapon == WeaponIndex.SwitchAxe or weapon == WeaponIndex.LightBowgun or weapon == WeaponIndex.HeavyBowgun:
            weapon_inner["sp"] = []
            for d in tr.find_all("td")[-2].find_all('div'):
                weapon_inner["sp"].append(d.text.strip())
            
            weapon_inner["sp"] = ",".join(weapon_inner["sp"])
            
        if weapon == WeaponIndex.LightBowgun or weapon == WeaponIndex.HeavyBowgun:
            pass
        else:
            img_element = tr.find_all('td')[4].find('img')
            if img_element is None:
                weapon_inner["element"] = "無"
                weapon_inner["element_attack"] = 0
            else:
                weapon_inner["element"] = get_element(img_element["src"])
                weapon_inner["element_attack"] = tr.find_all("td")[4].text
            
            if weapon != WeaponIndex.Bow:
                # Sharpness
                sharpness_div = tr.find_all("td")[6]
                lowest_sharpness = get_sharpness(sharpness_div.find_all("svg")[0])
                max_sharpness = get_sharpness(sharpness_div.find_all("svg")[1])
                
                weapon_inner["sharpness"] = lowest_sharpness
                weapon_inner["max_sharpness"] = max_sharpness
        
        weapon_inner["skills"] = []
        weapon_inner["needed_items"] = []
        weapon_inner["description"] = ""
        
        for div in tr.find_all("td")[-1].find_all("div"):
            splitted_skill = div.text.strip().split("+")
            skill_name = splitted_skill[0].strip()
            skill_level = int(splitted_skill[1].strip())
            skill_id = list(filter(lambda x, skill_name=skill_name: x[1] == skill_name, skills))[0][0]
            
            skill = {}
            skill["id"] = skill_id
            skill["level"] = skill_level
            weapon_inner["skills"].append(skill)        
            
        # Open subpage
        link = tr.find_all("td")[1].find("a")["href"]
        inner_page = requests.get(f"https://mhwilds.kiranico.com/{link}")
        inner_soup = BeautifulSoup(inner_page.text, "html.parser")
        desc = inner_soup.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div:nth-child(2) > blockquote > span")
        if desc is not None:
            weapon_inner["description"] = desc.text
        
        item_table = inner_soup.select_one("body > div > div > div > div.flex.flex-1.flex-col.gap-4.px-4.py-10 > div > div:nth-child(2) > div:nth-child(4) > div.relative.w-full.overflow-auto > table")
        
        if item_table is None:
            raise ValueError("Can't find item table")
    
        item_table_tr = item_table.find_all("tr")
        for item_tr in item_table_tr:
            item_td = item_tr.find_all("td")
            if len(item_td) == 0:
                continue
            
            item_name = item_td[0].text
            item_amount = int(item_td[1].text.replace("x", "").strip())
            item_id = list(filter(lambda x, item_name=item_name: x[1] == item_name, items))[0][0]
            
            weapon_inner["needed_items"].append({"id": item_id, "amount": item_amount})
        
        weapon_inner["icon_url"] = tr.find_all("td")[0].find("img")["src"]
        
        weapons[weapon.name].append(weapon_inner)
        
        
print(json.dumps(weapons, indent=4, ensure_ascii=False))