import json
import multiprocessing
import pathlib
import socket
import time
from static import utcs, hpsh
from typing import List, Literal
from urllib.parse import quote

import discord
from discord.ext import commands, tasks
from discord import app_commands, ForumChannel

import requests

API_KEY = "test_56797f716885307fe9cdd87915e3ac8607f13038efbe762a62236f8c3c8380daefe8d04e6d233bd35cf2fabdeb93fb0d"

BASE_URL = "https://open.api.nexon.com"

TW_OCID_API = BASE_URL + "/maplestorytw/v1/id"

CHARCTER_BASIC_API = BASE_URL + "/maplestorytw/v1/character/basic"


class Server(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.data_path = fr"{pathlib.Path(__file__).parent.resolve()}/data.json"
        with open(self.data_path) as j:
            self._data = json.load(j)

    def worker(self, idx, channel, return_dict) -> None:
        """worker"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s_start = time.time()
        host = channel
        port = host["port"]
        host = host["address"]

        try:
            s.connect((host, int(port)))
            s.shutdown(socket.SHUT_RD)

        except socket.timeout as err:
            s_runtime = "timeout"
        except OSError as err:
            s_runtime = "os error"
        except Exception as err:
            s_runtime = "unknown_error"
            print(f"Unknown error {channel}, {err}")
        else:
            s_runtime = (time.time() - s_start) * 1000
        return_dict[str(idx)+":"+channel['name']] = (
            f"{s_runtime:.2f}ms" if isinstance(s_runtime, float) else s_runtime
        )
        return

    async def refresh_server(self, server: str) -> dict:
        """multiprocessing because people are annoying"""
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        start = time.time()
        jobs = []
        for idx, channel in enumerate(self._data[server]):
            p = multiprocessing.Process(
                target=self.worker, args=(idx, channel, return_dict)
            )
            jobs.append(p)
            p.start()

        for proc in jobs:
            proc.join()

        print(
            f"[{self.__cog_name__}] {server} refreshed. ({time.time()-start:.4f} seconds)"
        )
        return return_dict

    @commands.hybrid_command(name="楓之谷伺服器狀態", description="")
    @app_commands.guilds(utcs, hpsh)
    async def maplestatus(self, ctx: commands.Context) -> None:
        selection = discord.ui.Select(placeholder="請選擇頻道", min_values=1, max_values=1)
        server = ["艾麗亞", "普力特", "琉德", "優依娜", "愛麗西亞", "殺人鯨", "Reboot", "Login"]

        for s in server:
            selection.add_option(label=s, value=s)

        async def callback(interaction: discord.Interaction):
            await interaction.response.defer(thinking=True)
            server = interaction.data["values"][0]
            re = await self.refresh_server(server)

            embed = discord.Embed(title=interaction.data["values"][0], color=0x00FF00)

            re = {k: v for k, v in sorted(re.items(), key=lambda item: int(item[0].split(':')[0]))}

            print(re)

            sss = ""

            for idx ,(k, v) in enumerate(re.items()):
                sss += f"**{k.split(':')[1]:>20}:** {v:8}\n"


            embed.description = sss
            await interaction.followup.send(embed=embed)
            # await interaction.response.send_message(embed=embed)


        selection.callback = callback

        view = discord.ui.View()
        view.add_item(selection)
        await ctx.send("請選擇頻道", view=view)

    @commands.hybrid_command(name="查詢台服楓之谷角色")
    @app_commands.guilds(utcs, hpsh)
    async def maplestorytw_char(self, ctx: commands.Context, character_name: str) -> None:
        """查詢台服楓之谷角色"""
        await ctx.defer()
        with requests.get(
            TW_OCID_API,
            params = {
                "character_name": character_name
            },
            headers = {
                'accept': 'application/json',
                "x-nxopen-api-key": f"{API_KEY}"
            },
        ) as resp:
            if resp.status_code != 200:
                return await ctx.send("取得角色ID失敗，請確認該角色名稱無誤")

            data = resp.json()
            char_id = data["ocid"]

            with requests.get(
                CHARCTER_BASIC_API,
                params = {
                    "ocid": char_id
                },
                headers = {
                    "x-nxopen-api-key": f"{API_KEY}"
                },
            ) as resp:
                if resp.status_code != 200:
                    return await ctx.send("無法取得角色資料")

                data = resp.json()

                embed = discord.Embed(
                    title=f"{data['character_name']} 的角色資訊",
                    color=0x00FF00,
                )
                embed.add_field(name="等級", value=data["character_level"])
                embed.add_field(name="職業", value=data["character_class"])
                embed.add_field(name="伺服器", value=data["world_name"])
                embed.add_field(name="創角時間", value=data["character_date_create"])
                embed.set_thumbnail(url=data["character_image"])

                await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Server(bot))
