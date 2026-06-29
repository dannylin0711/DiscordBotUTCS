from tqdm import tqdm
import json
import re
import sqlite3
from PIL import Image, ImageFile
import io
import os
from enum import Enum



item_json = open("items.json", "r", encoding="utf-8")
item_json = json.load(item_json)

db = sqlite3.connect("../cogs/asset/mhwilds.db")
c = db.cursor()


for item in tqdm(item_json):
    c.execute("INSERT INTO item (name, description, icon_url) VALUES (?, ?, ?)", (item["name"], item["description"], item["icon_url"]))  
    
db.commit()