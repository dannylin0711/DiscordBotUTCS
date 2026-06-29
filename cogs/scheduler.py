import asyncio
import datetime
import hashlib
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
from apscheduler.schedulers.asyncio import AsyncIOScheduler

ZZZ_NEWS_API = "https://sg-public-api-static.hoyoverse.com/content_v2_user/app/3e9196a4b9274bd7/getContentList?iPageSize=30&iPage=1&iChanId=296&sLangKey=zh-tw"

SUBMARINE_CABLE_INCIDENTS_JSON = "https://smc.peering.tw/data/incidents.json"

_ZZZ_SEEN_PATH = "zzz_news.json"
_INCIDENTS_SEEN_PATH = "submarine_incidents.json"

# Keep the persistent caches bounded so the bot doesn't get slower over time.
_MAX_ZZZ_SEEN = 5000
_MAX_INCIDENTS_SEEN = 20000

class Scheduler(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot:commands.Bot = bot

        # Prevent overlapping runs (which can accumulate if a job hangs) and coalesce
        # missed runs to a single execution.
        self.scheduler = AsyncIOScheduler(
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
            }
        )
        self.scheduler.add_job(
            self.get_zzz_news,
            "cron",
            minute="*",
            misfire_grace_time=5,
            id="get_zzz_news",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.submarine_incidents_schedule,
            "cron",
            minute="*",
            misfire_grace_time=5,
            id="submarine_incidents_schedule",
            replace_existing=True,
        )
        self.scheduler.start()

    def cog_unload(self):
        # Avoid waiting on long-running jobs while unloading/reloading the cog.
        self.scheduler.shutdown(wait=False)

    @staticmethod
    def _load_seen_map(path: str) -> dict[str, int]:
        """Load a bounded 'seen' cache.

        Supports legacy formats where the file contains a JSON list.
        """
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return {}

        if isinstance(data, dict):
            seen: dict[str, int] = {}
            for k, v in data.items():
                try:
                    seen[str(k)] = int(v)
                except Exception:
                    # If value isn't an int, treat as very old.
                    seen[str(k)] = 0
            return seen

        # Legacy list format.
        if isinstance(data, list):
            seen = {}
            for item in data:
                if isinstance(item, dict) and "iInfoId" in item:
                    seen[str(item["iInfoId"])] = 0
                else:
                    seen[str(item)] = 0
            return seen

        return {}

    @staticmethod
    def _save_seen_map(path: str, seen: dict[str, int]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(seen, f, ensure_ascii=False, indent=4)

    @staticmethod
    def _prune_seen_map(seen: dict[str, int], max_items: int) -> dict[str, int]:
        if len(seen) <= max_items:
            return seen
        # Keep the most recently seen items.
        items_sorted = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)
        return dict(items_sorted[:max_items])

    @staticmethod
    async def _fetch_json(url: str, timeout_s: float = 15.0):
        def _do_request():
            r = requests.get(url, timeout=timeout_s)
            r.raise_for_status()
            return r.json()

        return await asyncio.to_thread(_do_request)

    async def get_zzz_news(self):
        current_time = datetime.datetime.now()
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{time_str}:  Checking for ZZZ news...")

        bot = self.bot
        guild = bot.get_guild(516470319242805264)
        if guild is None:
            return

        thread = guild.get_thread(1272899951143424102)

        # thread = bot.get_channel(626624763141423134)

        if thread is None:
            return

        if not isinstance(thread, discord.Thread):
            return

        try:
            data = await self._fetch_json(ZZZ_NEWS_API, timeout_s=15.0)
        except Exception as e:
            print(f"Failed to fetch ZZZ news: {e}")
            return

        if "data" not in data:
            return

        news_list = data["data"]["list"]
        print("Fetched {} news items.".format(len(news_list)))
        pre_download_news = list(filter(lambda x: "預先下載" in x["sTitle"], news_list))
        print("Found {} pre-download news.".format(len(pre_download_news)))
        # Check news in json file
        seen = self._load_seen_map(_ZZZ_SEEN_PATH)
        seen_ids = set(seen.keys())
        new_news = [item for item in pre_download_news if str(item.get("iInfoId")) not in seen_ids]
        if len(new_news) == 0:
            return

        for news in new_news:
            title = news["sTitle"]
            content = news["sIntro"]

            img_json = json.loads(news.get("sExt"))
            embed = discord.Embed(title=title, color=0x00ff00)
            embed.set_image(url=img_json.get("news-banner")[0].get("url"))
            embed.add_field(name="內容", value=content, inline=False)
            await thread.send(embed=embed)

        now_ts = int(time.time())
        for news in new_news:
            seen[str(news.get("iInfoId"))] = now_ts
        seen = self._prune_seen_map(seen, _MAX_ZZZ_SEEN)
        self._save_seen_map(_ZZZ_SEEN_PATH, seen)

        return data["data"]["list"]

        # sent_news = old_news + [news['iInfoId'] for news in new_news]

        # with open("zzz_news.json", "w", encoding="utf-8") as f:
        #     json.dump(sent_news, f, ensure_ascii=False, indent=4)

        # return data["data"]["list"]
        #
    async def submarine_incidents_schedule(self):
        current_time = datetime.datetime.now()
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"{time_str}:  Checking for submarine cable incidents...")

        bot = self.bot
        guild = bot.get_guild(516470319242805264)
        if guild is None:
            return

        # TODO: Use a specific thread for submarine incidents
        channel = guild.get_channel(1435795074045968546)
        if channel is None:
            return

        if not isinstance(channel, discord.abc.Messageable):
            return

        try:
            incidents = await self._fetch_json(SUBMARINE_CABLE_INCIDENTS_JSON, timeout_s=15.0)
        except Exception as e:
            print(f"Failed to fetch submarine incidents: {e}")
            return

        print(f"Fetched {len(incidents)} incidents.")

        seen = self._load_seen_map(_INCIDENTS_SEEN_PATH)
        seen_hashes = set(seen.keys())

        new_incidents = []
        for incident in incidents:
            incident_str = json.dumps(incident, sort_keys=True)
            incident_hash = hashlib.sha256(incident_str.encode('utf-8')).hexdigest()
            if incident_hash not in seen_hashes:
                new_incidents.append((incident, incident_hash))

        if len(new_incidents) == 0:
            return

        for incident, incident_hash in new_incidents:
            title = incident.get("title", "N/A")
            description = incident.get("description", "N/A")
            status = incident.get("status", "N/A")
            cable_id = incident.get("cableid", "N/A")
            segment = incident.get("segment", "N/A")
            date = incident.get("date", "N/A")

            embed = discord.Embed(title=f"海纜事件：{title}", color=discord.Color.blue())
            embed.add_field(name="狀態", value=status, inline=True)
            embed.add_field(name="海纜 ID", value=cable_id, inline=True)
            embed.add_field(name="區段", value=segment, inline=True)
            embed.add_field(name="事件時間", value=date, inline=False)
            embed.add_field(name="描述", value=description, inline=False)

            await channel.send(embed=embed)

        now_ts = int(time.time())
        for _, incident_hash in new_incidents:
            seen[incident_hash] = now_ts
        seen = self._prune_seen_map(seen, _MAX_INCIDENTS_SEEN)
        self._save_seen_map(_INCIDENTS_SEEN_PATH, seen)


async def setup(bot: commands.Bot):
    await bot.add_cog(Scheduler(bot))
