from tqdm import tqdm
import json
import re
import sqlite3
from PIL import Image, ImageFile
import io
import os
from enum import Enum


weapon_json = open("weapon.json", "r", encoding="utf-8")
weapon_json = json.load(weapon_json)

db = sqlite3.connect("../cogs/asset/mhwilds.db")
c = db.cursor()


# CREATE TABLE "weapon"(
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     type TEXT NOT NULL,
#     description TEXT NOT NULL,
#     attack INTEGER NOT NULL,
#     affinity INTEGER NOT NULL,
#     element TEXT NOT NULL,
#     element_attack INTEGER NOT NULL,
#     sharpness TEXT NOT NULL,
#     max_sharpness TEXT NOT NULL,
#     slot1 INTEGER NOT NULL,
#     slot2 INTEGER NOT NULL,
#     slot3 INTEGER NOT NULL
# , `sp` TEXT, icon_url TEXT NOT NULL)

for weapon in weapon_json.values():
    sql_str = """
    INSERT INTO weapon (name, type, description, attack, affinity, element, element_attack, sharpness, max_sharpness, slot1, slot2, slot3, sp, icon_url)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    weapon_skill_sql = """
    INSERT INTO weapon_skills (weapon_id, skill_id, level)
    VALUES (?, ?, ?)
    """
    
    weapon_needed_item_sql = """
    INSERT INTO weapon_needed_items (weapon_id, item_id, quantity)
    VALUES (?, ?, ?)
    """
    
    for weapon_inner in weapon:
        
        if "sp" not in weapon_inner:
            weapon_inner["sp"] = ""
        
        if "element" not in weapon_inner:
            weapon_inner["element"] = ""
        if "element_attack" not in weapon_inner:
            weapon_inner["element_attack"] = 0
        if "sharpness" not in weapon_inner:
            weapon_inner["sharpness"] = ""
        if "max_sharpness" not in weapon_inner:
            weapon_inner["max_sharpness"] = ""
        
        
        
        c.execute(sql_str, (
            weapon_inner["name"],
            weapon_inner["type"],
            weapon_inner["description"],
            weapon_inner["attack"],
            weapon_inner["affinity"],
            weapon_inner["element"],
            weapon_inner["element_attack"],
            weapon_inner["sharpness"],
            weapon_inner["max_sharpness"],
            weapon_inner["slot1"],
            weapon_inner["slot2"],
            weapon_inner["slot3"],
            weapon_inner["sp"],
            weapon_inner["icon_url"]
        ))
        
        weapon_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        for skill in weapon_inner["skills"]:
            c.execute(weapon_skill_sql, (
                weapon_id,
                skill["id"],
                skill["level"]
            ))
            
        for item in weapon_inner["needed_items"]:
            c.execute(weapon_needed_item_sql, (
                weapon_id,
                item["id"],
                item["amount"]
            ))
        
        

db.commit()