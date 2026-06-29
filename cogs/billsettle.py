import discord
import os
import datetime
import time
import sqlite3
import pytz
import random
from datetime import timezone,timedelta
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord.utils import get
from discord import Guild
from discord import Client
from discord import opus
from discord import app_commands

from static import utcs, hpsh

startuptime = datetime.datetime.now()

allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=False)

class BillSettle(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        # SQLite-backed storage for bill splitting
        self.db = sqlite3.connect('cogs/asset/billsettle.db', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_db()

    # ----- helpers -----
    def _init_db(self):
        cur = self.db.cursor()
        # Ensure tables exist (will be no-ops if they already exist)
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS `settle` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                `name` TEXT,
                guild_id TEXT
            );
            CREATE TABLE IF NOT EXISTS `settle_bills` (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                `session_id` TEXT NOT NULL,
                `payer_id` INTEGER NOT NULL,
                `to_id` INTEGER,
                `amount` INTEGER NOT NULL,
                `note` TEXT,
                `is_shared` BOOLEAN NOT NULL
            );
            CREATE TABLE IF NOT EXISTS `settle_joins` (
                `settle_id` TEXT,
                `user_id` INTEGER,
                PRIMARY KEY (`session_id`, `user_id`)
            );
            """
        )
        self.db.commit()
        
    def _add_settle(self, name: str, guild_id: int) -> int:
        cur = self.db.cursor()
        cur.execute(
            """
            INSERT INTO `settle` (name, guild_id) VALUES (?, ?)
            """,
            (name, guild_id)
        )
        self.db.commit()
        if cur.lastrowid is None:
            raise RuntimeError("Failed to create new settle record.")
        return cur.lastrowid 
    
    def _get_settle(self, name: str) -> dict | None:
        cur = self.db.cursor()
        cur.execute(
            """
            SELECT * FROM `settle` WHERE name = ?
            """,
            (name,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)
    
    def _get_all_settles(self, guild_id: int) -> list[dict]:
        cur = self.db.cursor()
        cur.execute(
            """
            SELECT * FROM `settle` WHERE guild_id = ?
            """,
            (str(guild_id),)
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    
    def _is_user_in_settle(self, settle_id: int, user_id: int) -> bool:
        cur = self.db.cursor()
        cur.execute(
            """
            SELECT 1 FROM `settle_joins` WHERE settle_id = ? AND user_id = ?
            """,
            (settle_id, user_id)
        )
        return cur.fetchone() is not None
    
    @commands.hybrid_command(name="新增分帳筆記", with_app_command=True, description="新增一份分帳筆記")
    @app_commands.guilds(utcs, hpsh)
    async def 新增分帳筆記(self, ctx: commands.Context, name: str):
        """"""
        if ctx.guild is None:
            return await ctx.send("此指令只能在伺服器中使用。")
        guild_id = ctx.guild.id
        try:
            _ = self._add_settle(name, guild_id)
        except Exception as e:
            return await ctx.send(f"新增分帳筆記失敗: {e}")
        await ctx.send(f"已成功新增分帳筆記: {name}")
        
    @commands.hybrid_command(name="加入分帳", with_app_command=True, description="加入選定的分帳筆記")
    @app_commands.guilds(utcs, hpsh)
    async def 加入分帳(self, ctx: commands.Context):
        """"""
        if ctx.guild is None:
            return await ctx.send("此指令只能在伺服器中使用。")
        settles = self._get_all_settles(guild_id=ctx.guild.id)
        if not settles:
            return await ctx.send("目前沒有任何分帳筆記，請先使用 /新增分帳筆記 指令來新增。")
        
        selection_view = discord.ui.Select()
        selection_view.placeholder = "選擇一個分帳筆記"
        
        for settle in settles:
            selection_view.add_option(label=settle['name'], value=str(settle['id']))
            
        async def select_callback(interaction: discord.Interaction):
            selected_id = int(selection_view.values[0])
            selected_name = next((s['name'] for s in settles if s['id'] == selected_id), None)
            if selected_name is None:
                return await interaction.response.send_message("選擇的分帳筆記不存在。")
            # Add user to the selected settle
            cur = self.db.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO `settle_joins` (settle_id, user_id) VALUES (?, ?)
                    """,
                    (selected_id, ctx.author.id)
                )
                self.db.commit()
            except sqlite3.IntegrityError:
                return await interaction.response.send_message("你已經加入過這個分帳筆記了。")
            await interaction.response.send_message(f"你已成功加入分帳筆記: {selected_name}。")
        selection_view.callback = select_callback
        view = discord.ui.View()
        view.add_item(selection_view)
        await ctx.send("請選擇你要加入的分帳筆記:", view=view)
        
    @commands.hybrid_command(name="新增分帳項目", with_app_command=True, description="新增一筆分帳項目")
    @app_commands.guilds(utcs, hpsh)
    async def 新增分帳項目(self, ctx: commands.Context, amount: int, note: str = ""):
        """"""
        if ctx.guild is None:
            return await ctx.send("此指令只能在伺服器中使用。")
        settles = self._get_all_settles(guild_id=ctx.guild.id)
        if not settles:
            return await ctx.send("目前沒有任何分帳筆記，請先使用 /新增分帳筆記 指令來新增。")
        
        selection_view = discord.ui.Select()
        selection_view.placeholder = "選擇一個分帳筆記"
        for settle in settles:
            selection_view.add_option(label=settle['name'], value=str(settle['id']))
            
        selected_id = None
        to_id = None
            
        async def select_callback(interaction: discord.Interaction):
            nonlocal selected_id, to_id
            selected_id = int(selection_view.values[0])
            # Verify user is part of the selected settle
            cur = self.db.cursor()
            cur.execute(
                """
                SELECT 1 FROM `settle_joins` WHERE settle_id = ? AND user_id = ?
                """,
                (selected_id, ctx.author.id)
            )

            if cur.fetchone() is None:
                return await interaction.response.send_message("你尚未加入這個分帳筆記，無法新增項目。")
            # Add the bill item
            if to_id is None:
                is_shared = True
            else:
                is_shared = False
                
            if is_shared is True:
                to_id = ctx.author.id
            
            cur.execute(
                """
                INSERT INTO `settle_bills` (session_id, payer_id, to_id, amount, note, is_shared) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (selected_id, ctx.author.id, to_id, amount, note, is_shared)
            )
            self.db.commit()
            if ctx.guild is None:
                return await interaction.response.send_message("此指令只能在伺服器中使用。")            
            
            to_user = ctx.guild.get_member(to_id) if to_id else None
            
            if to_user is None:
                raise ValueError("指定的分帳對象不存在於此伺服器中。")
            
            additional_msg = ""
            
            if self._is_user_in_settle(selected_id, to_id) is False:
                cur.execute(
                    """
                    INSERT INTO `settle_joins` (settle_id, user_id) VALUES (?, ?)
                    """,
                    (selected_id, to_id)
                )
                self.db.commit()
                additional_msg = f"{to_user.name} 尚未加入此分帳筆記，已自動幫他加入。"
                
            if is_shared:
                await interaction.response.send_message(f"{additional_msg}已成功新增分帳項目: <@{ctx.author.id}> 支付 {amount} 元，所有人均攤，備註: {note}，是否分攤: 是", allowed_mentions=allowed_mentions)
            
            await interaction.response.send_message(f"{additional_msg}已成功新增分帳項目: <@{ctx.author.id}> 欠 <@{to_user.id}> {amount} 元，備註: {note}，是否分攤: {'是' if is_shared else '否'}", allowed_mentions=allowed_mentions)
        
        selection_view.callback = select_callback
        view = discord.ui.View()
        
        
        user_selection = discord.ui.UserSelect()
        user_selection.placeholder = "選擇要分帳給誰 (若不分帳給特定人則不選)"
        async def user_select_callback(interaction: discord.Interaction):
            nonlocal to_id
            if user_selection.values:
                to_id = user_selection.values[0].id
            else:
                to_id = None
            
            await interaction.response.send_message(f"已選擇分帳對象: @{to_id if to_id else '無'}，請接著選擇分帳筆記。", allowed_mentions=allowed_mentions)
            
        user_selection.callback = user_select_callback
        view.add_item(user_selection)
        view.add_item(selection_view)
        await ctx.send("請選擇你要新增項目的分帳筆記與對象，請先選擇分帳對象再選擇分帳筆記:", view=view)
        
    @commands.hybrid_command(name="查看分帳狀況", with_app_command=True, description="查看目前的分帳狀況")
    @app_commands.guilds(utcs, hpsh)
    async def 查看分帳狀況(self, ctx: commands.Context):
        """"""
        if ctx.guild is None:
            return await ctx.send("此指令只能在伺服器中使用。")
        settles = self._get_all_settles(guild_id=ctx.guild.id)
        if not settles:
            return await ctx.send("目前沒有任何分帳筆記，請先使用 /新增分帳筆記 指令來新增。")
        
        selection_view = discord.ui.Select()
        selection_view.placeholder = "選擇一個分帳筆記"
        for settle in settles:
            selection_view.add_option(label=settle['name'], value=str(settle['id']))
            
        async def select_callback(interaction: discord.Interaction):
            selected_id = int(selection_view.values[0])
            # Verify user is part of the selected settle
            cur = self.db.cursor()
            cur.execute(
                """
                SELECT 1 FROM `settle_joins` WHERE settle_id = ? AND user_id = ?
                """,
                (selected_id, ctx.author.id)
            )
            if cur.fetchone() is None:
                return await interaction.response.send_message("你尚未加入這個分帳筆記，無法查看狀況。")
            # Fetch and display bill items
            cur.execute(
                """
                SELECT * FROM `settle_bills` WHERE session_id = ?
                """,
                (selected_id,)
            )
            bills = cur.fetchall()
            if not bills:
                return await interaction.response.send_message("這個分帳筆記目前沒有任何項目。")
            message_lines = ["目前的分帳項目:"]
            for bill in bills:
                to_one = ctx.guild.get_member(bill['to_id'])
                pay_one = ctx.guild.get_member(bill['payer_id'])
                if is_shared := bill['is_shared']:
                    message_lines.append(f"- {bill['amount']} 元，由 <@{to_one.id}> 支付，所有人均攤，備註: {bill['note']}，是否分攤: 是")
                else:
                    message_lines.append(f"- {bill['amount']} 元，由 <@{to_one.id}> 支付，<@{pay_one.id}>欠款，備註: {bill['note']}，是否分攤: {'是' if bill['is_shared'] else '否'}")
            await interaction.response.send_message("\n".join(message_lines), allowed_mentions=allowed_mentions)
        
        selection_view.callback = select_callback
        view = discord.ui.View()
        view.add_item(selection_view)
        await ctx.send("請選擇你要查看的分帳筆記:", view=view)

    def cog_unload(self):
        try:
            self.db.close()
        except Exception:
            pass
        
        
        
        
        
async def setup(bot):
    await bot.add_cog(BillSettle(bot))