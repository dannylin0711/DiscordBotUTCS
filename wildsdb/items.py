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



test_url = "https://mhwilds.kiranico.com/zh-Hant/data/items"
response = requests.get(test_url)
soup = BeautifulSoup(response.text, "html.parser")

item_div = soup.select_one("body > div > div > div > div > div > div:nth-child(2) > div > div")
if item_div is None:
    exit()
    
item_a = item_div.children
items = []

for a in tqdm(item_a, desc="Items", total=len(item_div)):
    # print(a.text)
    
    inner_page = requests.get(f"https://mhwilds.kiranico.com/{a['href']}")
    inner_soup = BeautifulSoup(inner_page.text, "html.parser")
    
    description = ""
    
    description_span = inner_soup.select_one("body > div > div > div > div > div > div:nth-child(2) > div:nth-child(2) > blockquote")
    # print(description_span)
    if description_span is not None:
        description = description_span.text
        
    item = {}
    
    item["name"] = a.text
    item["description"] = description
    
    icon_url = a.find("img")["src"]
    
    item["icon_url"] = icon_url
    
    items.append(item)
    
print(json.dumps(items, indent=4, ensure_ascii=False))
    