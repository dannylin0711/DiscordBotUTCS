import random
from discord.ext import commands
from discord.ext.commands import Bot
from discord import app_commands

import discord
import asyncio
import opencc
import datetime

import requests

from static import utcs, hpsh
import re

from enum import Enum
from PIL import Image
from io import BytesIO
from colorthief import ColorThief

# ---------------------------------------------------------------------------
# nanoka (https://nanoka.cc) API endpoints.
#
# This cog was migrated from hakush.in (now offline) to nanoka.cc.
# The version to query is discovered at runtime from the manifest:
#   manifest.json -> {"zzz": {"latest": "3.1.3+...", "live": "3.0", ...}}
# All data lives under   https://static.nanoka.cc/zzz/<version>/...
# All images live under  https://static.nanoka.cc/assets/zzz/<icon>.webp
# ---------------------------------------------------------------------------
NANOKA_STATIC = "https://static.nanoka.cc"

MANIFEST_URL = NANOKA_STATIC + "/manifest.json"

# Data base, formatted with the resolved version string.
DATA_ENDPOINT = NANOKA_STATIC + "/zzz/{}"

# Every game asset is served as a webp under /assets/zzz keyed by its icon name.
CHARACTER_ICON = NANOKA_STATIC + "/assets/zzz/{}.webp"
WEAPON_ICON = NANOKA_STATIC + "/assets/zzz/{}.webp"
BOSS_ICON = NANOKA_STATIC + "/assets/zzz/{}.webp"

CHARACTER_JSON = "/character.json"
WEAPON_JSON = "/weapon.json"
SHIYU_JSON = "/shiyu.json"
DEADLY_ASSULT_JSON = "/boss.json"

CHARACTER_INFO = "/zh/character/{}.json"
WEAPON_INFO = "/zh/weapon/{}.json"
DEADLY_ASSULT_BOSS_JSON = "/zh/boss/{}.json"
SHIYU_DETAIL_JSON = "/zh/shiyu/{}.json"

converter = opencc.OpenCC('s2twp.json')


def resolve_version(version_key: str = "latest") -> str:
    """Resolve a friendly version key to the concrete nanoka version string.

    ``manifest.json`` exposes, for each game, a ``latest`` (newest datamine)
    and a ``live`` (current public build) version. We read the ``zzz`` entry.
    """
    manifest = requests.get(MANIFEST_URL).json()
    zzz = manifest["zzz"]
    if version_key == "live":
        return zzz.get("live", zzz["latest"])
    return zzz["latest"]


def data_base(version_key: str = "latest") -> str:
    """Return the data base url for the resolved version."""
    return DATA_ENDPOINT.format(resolve_version(version_key))


def resolve_bases() -> tuple[str, str]:
    """Return ``(latest_base, live_base)`` data urls from a single manifest fetch.

    ``latest`` is the newest datamine (test data we want to *display*); ``live``
    is the current public build (whose ``begin``/``end`` dates reflect the real
    in-game schedule, so it's what we use to *detect* the running period).
    """
    zzz = requests.get(MANIFEST_URL).json()["zzz"]
    latest = zzz["latest"]
    live = zzz.get("live", latest)
    return DATA_ENDPOINT.format(latest), DATA_ENDPOINT.format(live)


class CharacterEmbedType(Enum):
    BASIC_INFO = 0
    BASIC_ATTACK = 1
    DODGE = 2
    SPECIAL = 3
    CHAIN = 4
    ASSIST = 5
    PASSIVE = 6
    TALENT = 7
    BASIC_ATTACK_VALUE = 8
    DODGE_VALUE = 9
    SPECIAL_VALUE = 10
    CHAIN_VALUE = 11
    ASSIST_VALUE = 12


class Nanoka(commands.Cog):

    def __init__(self, bot:Bot):
        self.bot = bot
        self.charater_data = {}
        self.weapon_data = {}
        self.shiyu_data = {}
        self.deadly_assult_data = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(self.CharacterView({}))
        self.bot.add_view(self.ShiyuLevelSelectionView({}))
        self.bot.add_view(self.DriveView({}))
        self.bot.add_view(self.DeadlyAssultView({}))


    class CharacterView(discord.ui.LayoutView):

        container = discord.ui.Container()
        message: discord.Message = None

        def __init__(self, character_data:dict):
            super().__init__()
            self.character_data = character_data
            # Persistent-view registration passes an empty dict; nothing to build.
            if not character_data:
                return

            camp = list(character_data["camp"].values())[0]
            camp = converter.convert(camp)
            char_name = converter.convert(character_data["name"])
            icon = CHARACTER_ICON.format(character_data["icon"])

            section = discord.ui.Section(
                accessory=discord.ui.Thumbnail(media=icon),
            )
            section.add_item(discord.ui.TextDisplay(f"# {char_name}\n## {camp}"))

            self.container.add_item(section)

            self.content = []

            self.gallery = discord.ui.MediaGallery()
            for i in range(1, 4):
                img_url = CHARACTER_ICON.format(f"Mindscape_{character_data["id"]}_{i}")
                self.gallery.add_item(media=img_url)

        async def on_timeout(self) -> None:
            # Assuming the message is stored in self.message
            for child in self.children:
                if isinstance(child, discord.ui.ActionRow):
                    for btns in child.children:
                        btns.disabled = True

            self.container.add_item(discord.ui.TextDisplay(f"-# {'此互動已超時，請重新使用指令。'}"))

            if hasattr(self, 'message'):
                await self.message.edit(view=self)


        @classmethod
        def convert_str(cls, text:str) -> str:
            att_str = text.replace("<IconMap:Icon_Normal>", "<:zzz_attack:1343473689940856864>")
            att_str = att_str.replace("<IconMap:Icon_Evade>", "<:zzz_evade:1343473674748956732>")
            att_str = att_str.replace("<IconMap:Icon_Special>", "<:zzz_sp0:1417424824619241575>")
            att_str = att_str.replace("<IconMap:Icon_SpecialReady>", "<:zzz_sp:1343473641610018977>")
            att_str = att_str.replace("<IconMap:Icon_SpecialReady_Rp>", "<:zzz_sp2:1417424706826670160>")
            att_str = att_str.replace("<IconMap:Icon_UltimateReady>", "<:zzz_ult:1343473663202037841>")
            att_str = att_str.replace("<IconMap:Icon_Switch>", "<:zzz_switch:1343473628653813821>")

            att_str = re.sub(r"<color=#\w{6}>", "**", att_str)
            att_str = att_str.replace("</color>", "**")
            # Back-to-back / empty coloured spans (</color><color=...> or an empty
            # <color></color>) collapse to "****" — an empty bold that Discord renders
            # as a literal "**" and which desyncs every following bold marker. Merge
            # such runs so the surrounding text stays correctly bolded.
            while "****" in att_str:
                att_str = att_str.replace("****", "")
            att_str = att_str.replace("{LAYOUT_CONSOLECONTROLLER#操作杆}{LAYOUT_FALLBACK#摇杆}", "摇杆")

            # Replace CAL expressions like:
            # {CAL:900+AvatarSkillLevel(1)*0,1,2} or with trailing %.
            def replace_cal(match):
                raw = match.group('expr')
                # print(raw)
                # split into up to 3 parts: calc_expr, pad_number, pad_point
                parts = [p.strip() for p in raw.split(',')]
                calc_expr = parts[0] if parts else ''

                # Evaluate safely: allow only specific names/functions
                def avatar_skill_level(n):
                    try:
                        return 12
                    except Exception:
                        return 0

                safe_globals = {'__builtins__': None, 'AvatarSkillLevel': avatar_skill_level}
                # Validate calc_expr characters
                if not re.match(r'^[0-9A-Za-z_()+\-*/\.\s]*$', calc_expr):
                    print("Unsafe expression:", calc_expr)
                    return match.group(0)

                try:
                    val = eval(calc_expr, safe_globals, {})
                    if not isinstance(val, (int, float)):
                        return match.group(0)
                    val = float(val)
                except Exception:
                    return match.group(0)

                # Apply padding multiplier if provided
                show_percent = True
                if len(parts) >= 2 and parts[1] != '':
                    try:
                        pad_num = float(parts[1])
                    except Exception:
                        return match.group(0)
                    scaled = val * pad_num
                    # Round to nearest integer for padding step
                    scaled = round(scaled)
                    if pad_num == 1:
                        show_percent = False
                else:
                    # default: keep original value
                    scaled = val

                # Apply padding point formatting
                if len(parts) >= 3 and parts[2] != '':
                    try:
                        pad_point = int(parts[2])
                    except Exception:
                        return match.group(0)
                    formatted = f"{scaled:.{pad_point}f}"
                else:
                    # default 1 decimal place as previous behavior
                    formatted = f"{float(scaled):.1f}"

                return f"**{formatted}%**" if show_percent else f"**{formatted}**"

            att_str = re.sub(r"\{CAL:(?P<expr>[^\}]+)\}%?", replace_cal, att_str)

            att_str = converter.convert(att_str)

            return att_str

        def generate_embed(self, func: CharacterEmbedType):
            if self.gallery in self.children:
                self.remove_item(self.gallery)


            character_info = self.character_data

            if func == CharacterEmbedType.BASIC_INFO:
                self._generate_basic_info_embed(character_info)
            elif func == CharacterEmbedType.BASIC_ATTACK:
                self._generate_skill_embed(character_info, "basic")
            elif func == CharacterEmbedType.DODGE:
                self._generate_skill_embed(character_info, "dodge")
            elif func == CharacterEmbedType.SPECIAL:
                self._generate_skill_embed(character_info, "special")
            elif func == CharacterEmbedType.CHAIN:
                self._generate_skill_embed(character_info, "chain")
            elif func == CharacterEmbedType.ASSIST:
                self._generate_skill_embed(character_info, "assist")
            elif func == CharacterEmbedType.PASSIVE:
                self._generate_passive_embed(character_info)
            elif func == CharacterEmbedType.TALENT:
                self._generate_talent_embed(character_info)
            elif func == CharacterEmbedType.BASIC_ATTACK_VALUE:
                self._generate_skill_value_embed(character_info, "basic")
            elif func == CharacterEmbedType.DODGE_VALUE:
                self._generate_skill_value_embed(character_info, "dodge")
            elif func == CharacterEmbedType.SPECIAL_VALUE:
                self._generate_skill_value_embed(character_info, "special")
            elif func == CharacterEmbedType.CHAIN_VALUE:
                self._generate_skill_value_embed(character_info, "chain")
            elif func == CharacterEmbedType.ASSIST_VALUE:
                self._generate_skill_value_embed(character_info, "assist")


        def _generate_skill_value_embed(self, character_info: dict, skill_type: str):
            """Generate skill value embed, calculate the value"""
            for cont in self.content:
                self.container.remove_item(cont)

            skill_text_disp = discord.ui.TextDisplay("")
            skill_comb_text = ""
            for attack in character_info["skill"][skill_type]["description"]:
                if "param" not in attack.keys():
                    continue

                skill_name = self.convert_str(attack["name"])

                skill_comb_text += f"**{skill_name}**\n"

                skill_param = ""
                for idx, param in enumerate(attack["param"]):
                    matching = re.search(r"Skill:(\d+)", param["desc"])

                    if matching is None:
                        continue
                    matching = matching.group(1)
                    # print(matching)
                    if "param" not in param.keys():
                        continue
                    value_main = int(param["param"][matching]["main"])
                    value_growth = int(param["param"][matching]["growth"])
                    final_result = float(value_main + value_growth * 11)/100.0

                    converted_name = self.convert_str(param["name"])
                    skill_param += "{}: {:.2f}%\n".format(converted_name, final_result)

                skill_comb_text += skill_param + "\n"
                skill_text_disp.content = skill_comb_text

            self.container.add_item(skill_text_disp)
            self.content.append(skill_text_disp)



        def _generate_basic_info_embed(self, character_info: dict):
            if "partner_info" not in character_info.keys() or "profile_desc" not in character_info["partner_info"].keys():
                return

            for cont in self.content:
                self.container.remove_item(cont)

            skill_text_disp = discord.ui.TextDisplay("")
            skill_comb_text = ""

            skill_comb_text += f"### 角色類型: {converter.convert(list(character_info['weapon_type'].values())[0])}\n"
            skill_comb_text += f"### 角色介紹: {self.convert_str(character_info['partner_info']['profile_desc'])}\n"

            skill_text_disp.content = skill_comb_text
            self.container.add_item(skill_text_disp)
            self.content.append(skill_text_disp)


        def _generate_skill_embed(self, character_info: dict, skill_type: str):
            for cont in self.content:
                self.container.remove_item(cont)

            skill_text_disp = discord.ui.TextDisplay("")
            skill_comb_text = ""

            for attack in character_info["skill"][skill_type]["description"]:
                if "desc" not in attack.keys():
                    continue
                att_str = self.convert_str(attack["desc"])
                tag_line = self.convert_str(attack["name"])

                skill_comb_text += f"### {tag_line}\n{att_str}\n"

            skill_text_disp.content = skill_comb_text
            self.container.add_item(skill_text_disp)
            self.content.append(skill_text_disp)


        def _generate_passive_embed(self, character_info: dict):
            info = list(filter(lambda x: x['level'] == 7, character_info["passive"]["level"].values()))
            if len(info) == 1:
                info = info[0]
            else:
                with_potential = list(filter(lambda x: x.get('potential') and x['potential'][0] != 0, info))
                info = with_potential[0] if with_potential else info[0]


            reconstructed_dict = {value: info["desc"][idx] for idx, value in enumerate(info["name"])}

            for cont in self.content:
                self.container.remove_item(cont)

            skill_text_disp = discord.ui.TextDisplay("")
            skill_comb_text = ""

            for key, value in reconstructed_dict.items():
                att_str = self.convert_str(value)
                tag_line = self.convert_str(key)
                skill_comb_text += f"### {tag_line}\n{att_str}\n"

            skill_text_disp.content = skill_comb_text
            self.container.add_item(skill_text_disp)
            self.content.append(skill_text_disp)

        def _generate_talent_embed(self, character_info: dict):
            info = character_info["talent"]
            for cont in self.content:
                self.container.remove_item(cont)

            skill_text_disp = discord.ui.TextDisplay("")
            skill_comb_text = ""
            for key, value in info.items():
                talent_name = self.convert_str(value["name"])
                talent_desc = self.convert_str(value["desc"])
                talent_desc2 = self.convert_str(value["desc2"])

                talent_sp = ""

                for talent_sp_lines in talent_desc2.split("\n"):
                    talent_sp += "-# " + talent_sp_lines + "\n"

                skill_comb_text += f"### {talent_name}\n{talent_desc}\n\n{talent_sp}\n"

            skill_text_disp.content = skill_comb_text
            self.container.add_item(skill_text_disp)
            self.content.append(skill_text_disp)

            self.add_item(self.gallery)

        action_row_1 = discord.ui.ActionRow()

        @action_row_1.button(label="基本資料", style=discord.ButtonStyle.primary)
        async def basic_info(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(CharacterEmbedType.BASIC_INFO)
            await interaction.response.edit_message(view=self)

        action_row_2 = discord.ui.ActionRow()

        @action_row_2.button(label="普通攻擊", style=discord.ButtonStyle.primary)
        async def basic_attack(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            self.generate_embed(CharacterEmbedType.BASIC_ATTACK)
            await interaction.response.edit_message(view=self)

        @action_row_2.button(label="閃避", style=discord.ButtonStyle.primary)
        async def dodge(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            self.generate_embed(CharacterEmbedType.DODGE)
            await interaction.response.edit_message(view=self)

        @action_row_2.button(label="特殊技", style=discord.ButtonStyle.primary)
        async def skill(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            self.generate_embed(CharacterEmbedType.SPECIAL)
            await interaction.response.edit_message(view=self)

        @action_row_2.button(label="連攜技", style=discord.ButtonStyle.primary)
        async def chain(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            self.generate_embed(CharacterEmbedType.CHAIN)
            await interaction.response.edit_message(view=self)

        @action_row_2.button(label="支援", style=discord.ButtonStyle.primary)
        async def assist(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            self.generate_embed(CharacterEmbedType.ASSIST)
            await interaction.response.edit_message(view=self)

        action_row_3 = discord.ui.ActionRow()

        @action_row_3.button(label="普通攻擊 技能係數", style=discord.ButtonStyle.primary)
        async def basic_attack_value(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(CharacterEmbedType.BASIC_ATTACK_VALUE)
            await interaction.response.edit_message(view=self, embed=embed)

        @action_row_3.button(label="閃避 技能係數", style=discord.ButtonStyle.primary)
        async def dodge_value(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(CharacterEmbedType.DODGE_VALUE)
            await interaction.response.edit_message(view=self, embed=embed)

        @action_row_3.button(label="特殊技 技能係數", style=discord.ButtonStyle.primary)
        async def skill_value(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(CharacterEmbedType.SPECIAL_VALUE)
            await interaction.response.edit_message(view=self, embed=embed)

        @action_row_3.button(label="連攜技 技能係數", style=discord.ButtonStyle.primary)
        async def chain_value(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(CharacterEmbedType.CHAIN_VALUE)
            await interaction.response.edit_message(view=self, embed=embed)

        @action_row_3.button(label="支援 技能係數", style=discord.ButtonStyle.primary)
        async def assist_value(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(CharacterEmbedType.ASSIST_VALUE)
            await interaction.response.edit_message(view=self, embed=embed)

        action_row_4 = discord.ui.ActionRow()

        @action_row_4.button(label="核心技", style=discord.ButtonStyle.primary)
        async def core(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(CharacterEmbedType.PASSIVE)
            await interaction.response.edit_message(view=self, embed=embed)

        @action_row_4.button(label="意象影畫", style=discord.ButtonStyle.danger)
        async def talent(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(CharacterEmbedType.TALENT)
            await interaction.response.edit_message(view=self, embed=embed)




    @commands.hybrid_command(name="zzz角色", with_app_command=True, description="")
    @app_commands.rename(version="版本")
    @app_commands.choices(version=[
        app_commands.Choice(name="最新版本", value="latest"),
        app_commands.Choice(name="正式服版本", value="live"),
    ])
    async def getZZZCharater(self, ctx: commands.Context, version:str="latest"):
        """Get ZZZ Character"""
        await ctx.defer()

        base = data_base(version)
        with requests.get(base + CHARACTER_JSON) as response:
            self.charater_data = response.json()
        sorted_character = sorted(list(self.charater_data.keys()))
        async def selection_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            selection = interaction.data["values"][0]

            charater_info:dict = {}

            with requests.get(base + CHARACTER_INFO.format(selection)) as response:
                charater_info = response.json()

            view = self.CharacterView(charater_info)

            message_id = (await interaction.followup.send(view=view)).message_id
            view.message = await interaction.channel.fetch_message(message_id)

        selection_arr = []

        for _ in range(int(len(self.charater_data) / 20 + 1)):
            selection_arr.append(discord.ui.Select(placeholder="請選擇角色", min_values=1, max_values=1))

        for idx, charater in enumerate(sorted_character):
            ind = int(idx / 20)
            char_name = converter.convert(self.charater_data[charater]["zh"])
            # print(ind, char_name, charater)
            selection_arr[ind].add_option(label=char_name, value=charater)
            selection_arr[ind].callback = selection_callback

        view = discord.ui.View()
        for selection in selection_arr:
            if len(selection.options) > 0:
                view.add_item(selection)

        async def on_timeout():
            for child in view.children:
                if isinstance(child, discord.ui.Select):
                    child.disabled = True

            if hasattr(view, 'message'):
                await view.message.edit("此互動已超時，請重新使用指令。",view=view)
        view.on_timeout = on_timeout

        # print(view)
        sent_message = await ctx.send("請選擇角色", view=view)
        view.message = sent_message


    class DriveView(discord.ui.View):
        def __init__(self, drive_data:dict):
            super().__init__()
            self.drive_data = drive_data



    @commands.hybrid_command(name="zzz驅動盤洗洗樂", with_app_command=True, description="生成一張完全強化的驅動盤")
    @app_commands.guilds(utcs, hpsh)
    async def newDiskDrive(self, ctx: commands.Context):
        random.seed()
        position = random.randint(1, 6)

        embed = discord.Embed(title="驅動盤洗洗樂", description="驅動盤位置: {}".format(position), color=discord.Color.from_rgb(255, 255, 255))

        main_stat = ""

        if position == 1:
            main_stat = "生命值"
        elif position == 2:
            main_stat = "攻擊力"
        elif position == 3:
            main_stat = "防禦力"
        elif position == 4:
            main_stat = random.choice(["生命值%", "攻擊力%", "防禦力%", "暴擊率", "暴擊傷害", "異常精通"])
        elif position == 5:
            main_stat = random.choice(["生命值%", "攻擊力%", "防禦力%", "火屬性傷害加成", "物理傷害加成", "電屬性傷害加成", "冰屬性傷害加成", "以太傷害加成", "穿透率"])
        elif position == 6:
            main_stat = random.choice(["生命值%", "攻擊力%", "防禦力%", "衝擊力", "異常掌控", "能量自動回復"])

        embed.add_field(name="主屬性", value=main_stat, inline=False)
        sub_stat = ["生命值%", "攻擊力%", "防禦力%", "生命值", "攻擊力", "防禦力", "暴擊率", "暴擊傷害", "異常精通", "穿透值"]
        disk_sub = []

        if main_stat in sub_stat:
            sub_stat.remove(main_stat)

        random.shuffle(sub_stat)
        for _ in range(4):
            disk_sub.append(sub_stat.pop())

        enhance_time = random.randint(4, 5)

        stat_plus = [0,0,0,0]

        for _ in range(enhance_time):
            stat_plus[random.randint(0, 3)] += 1

        for idx, stat in enumerate(disk_sub):
            if stat_plus[idx] == 0:
                continue

            disk_sub[idx] += "+{}".format(stat_plus[idx])


        embed.add_field(name="副屬性", value=", ".join(disk_sub), inline=False)

        await ctx.send(embed=embed)



    @commands.hybrid_command(name="zzz音擎", with_app_command=True, description="查詢音擎資訊")
    @app_commands.guilds(utcs, hpsh)
    async def weapon_info(self, ctx: commands.Context) -> None:
        await ctx.defer()

        base = data_base("latest")
        with requests.get(base + WEAPON_JSON) as response:
            self.weapon_data = response.json()
        sorted_weapon = sorted(list(self.weapon_data.keys()))

        async def selection_callback(interaction: discord.Interaction):
            selection = interaction.data["values"][0]

            weapon_info:dict = {}

            with requests.get(base + WEAPON_INFO.format(selection)) as response:
                weapon_info = response.json()

            embed = discord.Embed(title=converter.convert(weapon_info["name"]), color=discord.Color.from_rgb(255, 255, 255))

            embed.add_field(name="武器類型", value=converter.convert(list(weapon_info["weapon_type"].values())[0]), inline=False)
            embed.add_field(name="武器介紹", value=converter.convert(self.CharacterView.convert_str(weapon_info["desc"])), inline=False)


            # (base_property.value + base_property.value * level["60"].rate / 10000 + base_property.value * stars["5"].star_rate / 10000) / 100
            attack_value = weapon_info["base_property"]["value"]
            attack_value += weapon_info["base_property"]["value"] * weapon_info["level"]["60"]["rate"] / 10000
            attack_value += weapon_info["base_property"]["value"] * weapon_info["stars"]["5"]["star_rate"] / 10000

            embed.add_field(name=converter.convert(weapon_info["base_property"]["name"]), value="{:.0f}".format(attack_value), inline=True)

            # rand_property.value + rand_property.value * stars["5"].rand_rate / 1e4
            rand_value = weapon_info["rand_property"]["value"]
            rand_value += weapon_info["rand_property"]["value"] * weapon_info["stars"]["5"]["rand_rate"] / 10000

            def apply_dotnet_percent_format(value, dotnet_format):
                if dotnet_format == "{0:0.#%}":
                    n = value / 100.0
                    formatted = f"{n:.1f}".rstrip('0').rstrip('.') + '%'
                    return formatted
                elif dotnet_format == "{0:0}":
                    return "{:.0f}".format(value)
                else:
                    raise NotImplementedError(f"Format '{dotnet_format}' not supported.")

            embed.add_field(name=converter.convert(weapon_info["rand_property"]["name"]).replace("覆","復"), value=apply_dotnet_percent_format(rand_value, weapon_info["rand_property"]["format"]), inline=True)

            embed.add_field(name="武器技能", value=self.CharacterView.convert_str("**"+converter.convert(weapon_info["talents"]["1"]["name"])+"**\n"+converter.convert(weapon_info["talents"]["1"]["desc"])), inline=False)


            embed.set_thumbnail(url=WEAPON_ICON.format(weapon_info["code_name"]))
            await interaction.response.send_message(embed=embed)

        selection_arr = []

        for _ in range(int(len(self.weapon_data) / 20 + 1)):
            selection_arr.append(discord.ui.Select(placeholder="請選擇音擎", min_values=1, max_values=1))

        for idx, weapon in enumerate(sorted_weapon):
            ind = int(idx / 20)
            # print(ind)
            weapon_name = converter.convert(self.weapon_data[weapon]["zh"])

            selection_arr[ind].add_option(label=weapon_name, value=weapon)
            selection_arr[ind].callback = selection_callback

        view = discord.ui.View()
        for selection in selection_arr:
            view.add_item(selection)
        await ctx.send("請選擇音擎", view=view)

    class ShiyuLevelSelectionView(discord.ui.View):
        def __init__(self, shiyu_data:dict):
            super().__init__()
            self.shiyu_data = shiyu_data
            # Persistent-view registration passes an empty dict; nothing to build.
            if not shiyu_data:
                return

            if len(str(shiyu_data["id"])) == 6:
                self.shiyu_data["id"] = shiyu_data["id"] // 10

            for level in range(1, 8):
                if "{}{:02d}".format(self.shiyu_data["id"], level) not in self.shiyu_data["zone"].keys():
                    self.find_item(level).disabled = True

            if "{}{:02d}1".format(self.shiyu_data["id"], 5) in self.shiyu_data["zone"].keys():
                self.find_item(5).disabled = True
                btn = discord.ui.Button(label="5-1", style=discord.ButtonStyle.primary, id=51)
                btn.callback = self.generate_lv51_extends
                self.add_item(btn)

            if "{}{:02d}2".format(self.shiyu_data["id"], 5) in self.shiyu_data["zone"].keys():
                self.find_item(5).disabled = True
                btn = discord.ui.Button(label="5-2", style=discord.ButtonStyle.primary, id=52)
                btn.callback = self.generate_lv52_extends
                self.add_item(btn)

            if "{}{:02d}3".format(self.shiyu_data["id"], 5) in self.shiyu_data["zone"].keys():
                self.find_item(5).disabled = True
                btn = discord.ui.Button(label="5-3", style=discord.ButtonStyle.primary, id=53)
                btn.callback = self.generate_lv53_extends
                self.add_item(btn)


        @classmethod
        def convert_str(cls, att_str:str) -> str:

            att_str = re.sub(r"<color=#\w{6}>", "**", att_str)
            att_str = att_str.replace("</color>", "**")
            # Back-to-back / empty coloured spans (</color><color=...> or an empty
            # <color></color>) collapse to "****" — an empty bold that Discord renders
            # as a literal "**" and which desyncs every following bold marker. Merge
            # such runs so the surrounding text stays correctly bolded.
            while "****" in att_str:
                att_str = att_str.replace("****", "")
            att_str = att_str.replace("{LAYOUT_CONSOLECONTROLLER#操作杆}{LAYOUT_FALLBACK#摇杆}", "摇杆")

            def replace_cal(match):
                raw = match.group('expr')
                parts = [p.strip() for p in raw.split(',')]
                calc_expr = parts[0] if parts else ''

                def avatar_skill_level(n):
                    try:
                        return 12
                    except Exception:
                        return 0

                safe_globals = {'__builtins__': None, 'AvatarSkillLevel': avatar_skill_level}
                if not re.match(r'^[0-9A-Za-z_()+\-*/\.\s]*$', calc_expr):
                    return match.group(0)
                try:
                    val = eval(calc_expr, safe_globals, {})
                    if not isinstance(val, (int, float)):
                        return match.group(0)
                    val = float(val)
                except Exception:
                    return match.group(0)

                show_percent = True
                if len(parts) >= 2 and parts[1] != '':
                    try:
                        pad_num = float(parts[1])
                    except Exception:
                        return match.group(0)
                    scaled = round(val * pad_num)
                    if pad_num == 1:
                        show_percent = False
                else:
                    scaled = val

                if len(parts) >= 3 and parts[2] != '':
                    try:
                        pad_point = int(parts[2])
                    except Exception:
                        return match.group(0)
                    formatted = f"{scaled:.{pad_point}f}"
                else:
                    formatted = f"{float(scaled):.1f}"

                return f"**{formatted}%**" if show_percent else f"**{formatted}**"

            att_str = re.sub(r"\{CAL:(?P<expr>[^\}]+)\}%?", replace_cal, att_str)

            att_str = converter.convert(att_str)
            return att_str

        @discord.ui.button(label="1", style=discord.ButtonStyle.primary, id=1)
        async def button_lv1(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(1)
            await interaction.response.edit_message(view=self, embed=embed)

        @discord.ui.button(label="2", style=discord.ButtonStyle.primary, id=2)
        async def button_lv2(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(2)
            await interaction.response.edit_message(view=self, embed=embed)

        @discord.ui.button(label="3", style=discord.ButtonStyle.primary, id=3)
        async def button_lv3(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(3)
            await interaction.response.edit_message(view=self, embed=embed)

        @discord.ui.button(label="4", style=discord.ButtonStyle.primary, id=4)
        async def button_lv4(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(4)
            await interaction.response.edit_message(view=self, embed=embed)

        @discord.ui.button(label="5", style=discord.ButtonStyle.primary, id=5)
        async def button_lv5(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(5)
            await interaction.response.edit_message(view=self, embed=embed)

        @discord.ui.button(label="6", style=discord.ButtonStyle.primary, id=6)
        async def button_lv6(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(6)
            await interaction.response.edit_message(view=self, embed=embed)

        @discord.ui.button(label="7", style=discord.ButtonStyle.primary, id=7)
        async def button_lv7(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            embed = self.generate_embed(7)
            await interaction.response.edit_message(view=self, embed=embed)




        def get_chinese(self, input: str) -> str:
            """Convert input to Chinese characters."""
            if input == "fire":
                return "火"
            elif input == "physical":
                return "物理"
            elif input == "electric":
                return "電"
            elif input == "ice":
                return "冰"
            elif input == "ether":
                return "以太"
            elif input == "wind":
                return "風"
            else:
                return input

        async def generate_lv51_extends(self, interaction: discord.Interaction):
            embed = self.generate_lv5_extends(1)
            await interaction.response.edit_message(view=self, embed=embed)

        async def generate_lv52_extends(self, interaction: discord.Interaction):
            embed = self.generate_lv5_extends(2)
            await interaction.response.edit_message(view=self, embed=embed)

        async def generate_lv53_extends(self, interaction: discord.Interaction):
            embed = self.generate_lv5_extends(3)
            await interaction.response.edit_message(view=self, embed=embed)

        def generate_lv5_extends(self, ext_level: int):
            embed = self.generate_embed(ext_level, sub=True)
            return embed

        def generate_embed(self, level: int, sub: bool = False) -> discord.Embed:
            if sub:
                shiyu = self.shiyu_data["zone"]["{}{:02d}{}".format(self.shiyu_data["id"], 5, level)]
            else:
                shiyu = self.shiyu_data["zone"]["{}{:02d}".format(self.shiyu_data["id"], level)]

            embed = discord.Embed(title=converter.convert(shiyu["name"]), color=discord.Color.from_rgb(255, 255, 255))
            shiyu_id = self.shiyu_data["id"]
            embed.set_footer(text="第 {} 期 ・ ID: {}".format(int(str(shiyu_id)[3:]), shiyu_id))
            buff = list(shiyu["layer_buff"].values())
            for b in buff:
                embed.add_field(name="增益效果", value="**{}:**\n{}".format(self.convert_str(b["title"]), self.convert_str(b["desc"])), inline=False)

            high_weak = {"fire": False, "physical": False, "electric": False, "ice": False, "ether": False, "wind": False}
            high_resist = {"fire": False, "physical": False, "electric": False, "ice": False, "ether": False, "wind": False}

            low_weak = {"fire": False, "physical": False, "electric": False, "ice": False, "ether": False, "wind": False}
            low_resist = {"fire": False, "physical": False, "electric": False, "ice": False, "ether": False, "wind": False}


            high_room = list(shiyu["layer_room"].values())[0]

            for monster in high_room["monster_list"].values():
                for ele , stat in monster["element"].items():
                    if stat == 1:
                        high_weak[ele.lower()] = True
                    elif stat == -1:
                        high_resist[ele.lower()] = True

            low_room = list(shiyu["layer_room"].values())[-1]
            for monster in low_room["monster_list"].values():
                for ele , stat in monster["element"].items():
                    if stat == 1:
                        low_weak[ele.lower()] = True
                    elif stat == -1:
                        low_resist[ele.lower()] = True

            high_weak_repr = ", ".join([self.get_chinese(key) for key, value in high_weak.items() if value])
            high_resist_repr = ", ".join([self.get_chinese(key) for key, value in high_resist.items() if value])

            low_weak_repr = ", ".join([self.get_chinese(key) for key, value in low_weak.items() if value])
            low_resist_repr = ", ".join([self.get_chinese(key) for key, value in low_resist.items() if value])

            embed.add_field(name="上半弱點", value=high_weak_repr if len(high_weak_repr) != 0 else "無", inline=True)
            embed.add_field(name="上半抗性", value=high_resist_repr if len(high_resist_repr) != 0 else "無", inline=True)
            embed.add_field(name=" ", value=" ", inline=True)  # Empty field for spacing
            embed.add_field(name="下半弱點", value=low_weak_repr if len(low_weak_repr) != 0 else "無", inline=True)
            embed.add_field(name="下半抗性", value=low_resist_repr if len(low_resist_repr) != 0 else "無", inline=True)
            embed.add_field(name=" ", value=" ", inline=True)  # Empty field for spacing

            return embed

    @commands.hybrid_command(name="zzz式輿", with_app_command=True, description="查詢式輿防衛戰資訊")
    @app_commands.rename(now="期數")
    @app_commands.describe(now="不輸入或-1為當前期數式輿防衛戰，輸入其他數字為指定期數式輿防衛戰")
    @app_commands.guilds(utcs, hpsh)
    async def shiyu_info(self, ctx: commands.Context, now: int = -1) -> None:
        """"""
        await ctx.defer()

        latest_base, live_base = resolve_bases()

        if now == -1:
            def current_filter(item):
                shiyu_id, shiyu = item

                if not isinstance(shiyu, dict) or "begin" not in shiyu or "end" not in shiyu:
                    return False

                # Parse dates and add UTC+8 timezone
                tz = datetime.timezone(datetime.timedelta(hours=8))
                begin_date = datetime.datetime.strptime(shiyu["begin"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
                end_date = datetime.datetime.strptime(shiyu["end"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
                current_time = datetime.datetime.now(tz)

                # Check if current time is within the event period
                return begin_date <= current_time <= end_date

            # Detect the running period from the LIVE schedule (real in-game dates).
            with requests.get(live_base + SHIYU_JSON) as response:
                live_list = response.json()
            current_shiyu = dict(filter(current_filter, live_list.items()))
            if current_shiyu:
                # Most recent matching period.
                shiyu_id = max(current_shiyu.keys(), key=lambda k: int(k))
                # ...but display the newest (test) data for that period.
                with requests.get(latest_base + SHIYU_DETAIL_JSON.format(shiyu_id)) as response:
                    shiyu_info = response.json()

                    view = self.ShiyuLevelSelectionView(shiyu_info)
                    await ctx.send(view=view)
            else:
                await ctx.send("目前沒有正在進行的式輿防衛戰")
        else:
            with requests.get(latest_base + SHIYU_JSON) as response:
                self.shiyu_data = response.json()
            shiyu_id = "620{:d}".format(now)
            if shiyu_id in self.shiyu_data:
                with requests.get(latest_base + SHIYU_DETAIL_JSON.format(shiyu_id)) as response:
                    shiyu_info = response.json()

                    view = self.ShiyuLevelSelectionView(shiyu_info)
                    await ctx.send(view=view)
            else:
                await ctx.send("查無此期數式輿防衛戰")

    class DeadlyAssultView(discord.ui.LayoutView):
        def __init__(self, deadly_assult_data:dict):
            super().__init__()
            self.deadly_assult_data = deadly_assult_data
            # Persistent-view registration passes an empty dict; nothing to build.
            if not deadly_assult_data:
                return
            self.buff_container = discord.ui.Container()
            self.action_row = discord.ui.ActionRow()
            self.boss_container = discord.ui.Container()

            for idx, i in enumerate(self.deadly_assult_data["zone"].values()):
                async def btn_callback(interaction: discord.Interaction, page_idx=idx):
                    page = page_idx
                    self.generate_boss_info(page + 1)
                    await interaction.response.edit_message(view=self)

                btn = discord.ui.Button(label=converter.convert(i["name"]), style=discord.ButtonStyle.primary)
                btn.callback = btn_callback
                self.action_row.add_item(btn)


            buff_text = ""

            for zone in self.deadly_assult_data["zone"].values():
                for buff in zone["selectable_buff"].values():
                    buff_text += "## {}\n{}\n\n".format(converter.convert(buff["title"]), self.convert_str(buff["desc"]))
                break

            boss_id = self.deadly_assult_data["id"]
            difficulty = "困難模式" if self.deadly_assult_data.get("zone_type") == 1002 else "普通模式"
            info_disp = discord.ui.TextDisplay(
                "# {}\n-# 第 {} 期 ・ {} ・ ID: {}".format(
                    converter.convert(self.deadly_assult_data["name"]),
                    int(str(boss_id)[2:5]), difficulty, boss_id))
            self.buff_container.add_item(info_disp)

            buff_text_disp = discord.ui.TextDisplay(buff_text)
            self.buff_container.add_item(buff_text_disp)

            self.add_item(self.buff_container)
            self.add_item(self.action_row)
            # self.add_item(self.boss_container)

        @classmethod
        def convert_str(cls, att_str:str) -> str:

            att_str = re.sub(r"<color=#\w{6}>", "**", att_str)
            att_str = att_str.replace("</color>", "**")
            # Back-to-back / empty coloured spans (</color><color=...> or an empty
            # <color></color>) collapse to "****" — an empty bold that Discord renders
            # as a literal "**" and which desyncs every following bold marker. Merge
            # such runs so the surrounding text stays correctly bolded.
            while "****" in att_str:
                att_str = att_str.replace("****", "")
            att_str = att_str.replace("{LAYOUT_CONSOLECONTROLLER#操作杆}{LAYOUT_FALLBACK#摇杆}", "摇杆")

            def replace_cal(match):
                raw = match.group('expr')
                parts = [p.strip() for p in raw.split(',')]
                calc_expr = parts[0] if parts else ''

                def avatar_skill_level(n):
                    try:
                        return 12
                    except Exception:
                        return 0

                safe_globals = {'__builtins__': None, 'AvatarSkillLevel': avatar_skill_level}
                if not re.match(r'^[0-9A-Za-z_()+\-*/\.\s]*$', calc_expr):
                    return match.group(0)
                try:
                    val = eval(calc_expr, safe_globals, {})
                    if not isinstance(val, (int, float)):
                        return match.group(0)
                    val = float(val)
                except Exception:
                    return match.group(0)

                show_percent = True
                if len(parts) >= 2 and parts[1] != '':
                    try:
                        pad_num = float(parts[1])
                    except Exception:
                        return match.group(0)
                    scaled = round(val * pad_num)
                    if pad_num == 1:
                        show_percent = False
                else:
                    scaled = val

                if len(parts) >= 3 and parts[2] != '':
                    try:
                        pad_point = int(parts[2])
                    except Exception:
                        return match.group(0)
                    formatted = f"{scaled:.{pad_point}f}"
                else:
                    formatted = f"{float(scaled):.1f}"

                return f"**{formatted}%**" if show_percent else f"**{formatted}**"

            att_str = re.sub(r"\{CAL:(?P<expr>[^\}]+)\}%?", replace_cal, att_str)

            att_str = converter.convert(att_str)
            return att_str

        def get_chinese(self, input: str) -> str:
            """Convert input to Chinese characters."""
            if input == "fire":
                return "火"
            elif input == "physical":
                return "物理"
            elif input == "electric":
                return "電"
            elif input == "ice":
                return "冰"
            elif input == "ether":
                return "以太"
            elif input == "wind":
                return "風"
            else:
                return input

        def generate_boss_info(self, page: int):
            for cont in self.boss_container.children:
                self.boss_container.remove_item(cont)

            zone = list(self.deadly_assult_data["zone"].values())[page - 1]

            special_effects = '\n'.join([layer["desc"] for layer in zone["layer_buff"].values()])
            boss_adjust:dict = self.deadly_assult_data["boss_adjust"]
            # Difficulty levels live in two blocks: normal mode = keys 1001-1029 (10xx,
            # 29 levels), hard mode = keys 1301-1324 (13xx, 24 levels). The detail bundles
            # both; its top-level zone_type (1002 = hard) selects which block applies.
            if self.deadly_assult_data.get("zone_type") == 1002:
                level_keys = sorted((k for k in boss_adjust if 1300 < int(k) < 2000), key=int)
            else:
                level_keys = sorted((k for k in boss_adjust if 1000 < int(k) < 1300), key=int)
            num_levels = len(level_keys)
            total_adj = sum(boss_adjust[k]["hp"] for k in level_keys) / 10000


            monster = list(list(zone["layer_room"].values())[0]["monster_list"].values())[0]
            atk_adj = (1 + boss_adjust[level_keys[-1]]["atk"] / 10000) * monster["stats"]["attack"]
            thumb = BOSS_ICON.format(monster["image"].split("/")[-1][:-4])

            monster_weak = []
            for ele, stat in monster["element"].items():
                if stat == 1:
                    monster_weak.append(self.get_chinese(ele.lower()))
            monster_weak_str = ", ".join(monster_weak) if len(monster_weak) != 0 else "無"

            monster_resist = []
            for ele, stat in monster["element"].items():
                if stat == -1:
                    monster_resist.append(self.get_chinese(ele.lower()))
            monster_resist_str = ", ".join(monster_resist) if len(monster_resist) != 0 else "無"


            # print(thumb)

            section = discord.ui.Section(accessory=discord.ui.Thumbnail(media=thumb))
            section.add_item(discord.ui.TextDisplay("# Boss效果\n{}".format(converter.convert(self.convert_str(special_effects)))))

            boss_info_str = """-# Boss資訊 第{0}條狀況下
-# 1~{0} 累計總血量: {1}
-# 攻擊: {2}
-# 防禦: {3}
-# 失衡: {4}
-# 異常條遞增: {5}%
-# 弱點: {6}
-# 抗性: {7}""".format(
                num_levels,
                total_adj * monster["stats"]["hp"],
                atk_adj,
                monster["stats"]["defence"],
                monster["stats"]["stun"],
                monster["stats"]["attribute_infliction"],
                monster_weak_str,
                monster_resist_str
            )

            section.add_item(discord.ui.TextDisplay(boss_info_str))

            self.boss_container.add_item(section)

            if self.boss_container not in self.children:
                self.add_item(self.boss_container)

    @commands.hybrid_command(name="zzz危局", with_app_command=True, description="查詢危局強襲戰資訊")
    @app_commands.rename(now="期數")
    @app_commands.describe(now="不輸入或-1為當前期數危局強襲戰，輸入其他數字為指定期數危局強襲戰")
    @app_commands.guilds(utcs, hpsh)
    async def deadly_assult_info(self, ctx: commands.Context, now: int = -1) -> None:
        """"""
        await ctx.defer()

        latest_base, live_base = resolve_bases()

        if now == -1:
            def current_filter(item):
                boss_id, boss = item

                if not isinstance(boss, dict) or "begin" not in boss or "end" not in boss:
                    return False

                # Only show the standard (non hard-mode) rotation. zone_type 1002 is hard mode.
                if boss.get("zone_type") == 1002:
                    return False

                # Parse dates and add UTC+8 timezone
                tz = datetime.timezone(datetime.timedelta(hours=8))
                begin_date = datetime.datetime.strptime(boss["begin"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
                end_date = datetime.datetime.strptime(boss["end"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
                current_time = datetime.datetime.now(tz)

                # Check if current time is within the event period
                return begin_date <= current_time <= end_date

            # Detect the running period from the LIVE schedule (real in-game dates).
            with requests.get(live_base + DEADLY_ASSULT_JSON) as response:
                live_list = response.json()
            current_bosses = dict(filter(current_filter, live_list.items()))

            if current_bosses:
                # Most recent matching period.
                filtered_boss_id = max(current_bosses.keys(), key=lambda k: int(k))
                boss_info = {}

                # ...but display the newest (test) data for that period.
                boss_info_json = DEADLY_ASSULT_BOSS_JSON.format(filtered_boss_id)
                with requests.get(latest_base + boss_info_json) as response:
                    boss_info = response.json()

                view = self.DeadlyAssultView(boss_info)

                await ctx.send(view=view)
            else:
                await ctx.send("目前沒有正在進行的危局")

        elif now == 0 or now <= -2:
            await ctx.send("輸入錯誤，請輸入正確的參數")
        else:
            # Boss id scheme differs by era: older periods are 5-digit "69<period>",
            # newer ones are "69<period>1" (slot 1, standard mode). Try both.
            boss_info = None
            for candidate in ("69{:03d}1".format(now), "69{:03d}".format(now)):
                response = requests.get(latest_base + DEADLY_ASSULT_BOSS_JSON.format(candidate))
                if response.status_code == 200:
                    boss_info = response.json()
                    break
            if boss_info:
                view = self.DeadlyAssultView(boss_info)
                await ctx.send(view=view)
            else:
                await ctx.send("查無此期數危局強襲戰")



async def setup(bot):
    await bot.add_cog(Nanoka(bot))
