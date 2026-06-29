import discord
from discord.ext import commands, tasks
from discord import app_commands, ForumChannel
from static import utcs, hpsh
import asyncio


import io
import requests
from urllib.parse import quote
import os
import json
import calendar
import datetime


from PIL import Image, ImageFile

class LineSticker(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.count = 0
        
        
    class StickerSelectView(discord.ui.LayoutView):
        class StickerSendButton(discord.ui.Button):
            def __init__(self, sticker_id: str, data: dict, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.data = data
                self.sticker_id = sticker_id
                
            async def callback(self, interaction: discord.Interaction):
                # Button interactions must be acknowledged quickly (<=3s).
                await interaction.response.defer(thinking=True)

                current_sticker_id = self.sticker_id

                if 'hasAnimation' in self.data.keys():
                    if self.data['hasAnimation']:
                        def _download_and_convert_to_gif_bytes() -> bytes:
                            real_sticker_png = requests.get(
                                "https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iPhone/sticker_animation.png".format(
                                    current_sticker_id
                                ),
                                stream=True,
                                timeout=20,
                            )
                            arr = io.BytesIO(real_sticker_png.content)
                            arr.seek(0)

                            ori_apng = Image.open(arr)
                            frames: list[Image.Image] = []
                            for i in range(ori_apng.n_frames):
                                ori_apng.seek(i)
                                frames.append(ori_apng.copy().convert("RGBA"))

                            output = io.BytesIO()
                            frames[0].save(
                                output,
                                format="GIF",
                                save_all=True,
                                disposal=2,
                                append_images=frames[1:],
                                loop=0,
                            )
                            return output.getvalue()

                        try:
                            gif_bytes = await asyncio.to_thread(_download_and_convert_to_gif_bytes)
                        except Exception:
                            return await interaction.followup.send(
                                "貼圖轉換失敗，請稍後再試。"
                            )

                        output = io.BytesIO(gif_bytes)
                        output.seek(0)
                        await interaction.followup.send(
                            file=discord.File(output, filename="file.gif")
                        )
                        return

                    tmp_view = discord.ui.LayoutView()
                    tmp_gallery = discord.ui.MediaGallery()
                    tmp_gallery.add_item(
                        media="https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iphone/sticker.png".format(
                            current_sticker_id
                        )
                    )
                    tmp_view.add_item(tmp_gallery)
                    await interaction.followup.send(view=tmp_view)
        
        
        def __init__(self, sticker_json: dict) -> None:
            super().__init__()
            self.data = sticker_json
            self.page = 0
            
            self.total_page = len(sticker_json['stickers']) // 4 + (1 if len(sticker_json['stickers']) % 4 > 0 else 0)
            
            self._setup_initial_gallery()
            
            
        gallery = discord.ui.MediaGallery()
        
        action_row = discord.ui.ActionRow()
        
        send_row = discord.ui.ActionRow()
        
        @action_row.button(label="上一頁", style=discord.ButtonStyle.primary, disabled=True)
        async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page > 0:
                self.page -= 1
                await self.update_gallery(interaction)
                
        @action_row.button(label="下一頁", style=discord.ButtonStyle.primary)
        async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.page < self.total_page - 1:
                self.page += 1
                await self.update_gallery(interaction)
                
        def _setup_initial_gallery(self):
            self.gallery.clear_items()
            start_idx = self.page * 4
            end_idx = start_idx + 4
            
            self.send_row.clear_items()
            
            for idx, sticker in enumerate(self.data['stickers'][start_idx:end_idx]):
                sticker_id = sticker['id']
                self.gallery.add_item(media="https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iphone/sticker.png".format(sticker_id))
                
                temp_btn = discord.ui.Button(label=f"{start_idx + idx + 1}", style=discord.ButtonStyle.primary)
                temp_btn = self.StickerSendButton(sticker_id, self.data, label=f"{start_idx + idx + 1}", style=discord.ButtonStyle.primary)
                self.send_row.add_item(temp_btn)

        async def update_gallery(self, interaction: discord.Interaction):
            self.gallery.clear_items()
            start_idx = self.page * 4
            end_idx = start_idx + 4
            
            self.send_row.clear_items()
            
            for idx, sticker in enumerate(self.data['stickers'][start_idx:end_idx]):
                sticker_id = sticker['id']
                self.gallery.add_item(media="https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iphone/sticker.png".format(sticker_id))

                temp_btn = discord.ui.Button(label=f"{start_idx + idx + 1}", style=discord.ButtonStyle.primary)
                temp_btn = self.StickerSendButton(sticker_id, self.data, label=f"{start_idx + idx + 1}", style=discord.ButtonStyle.primary)
                self.send_row.add_item(temp_btn)
                
            self.action_row.children[0].disabled = (self.page == 0)
            self.action_row.children[1].disabled = (self.page == self.total_page - 1)
            
            await interaction.response.edit_message(view=self)
        
    class StickerModal(discord.ui.Modal, title="貼圖資訊"):
        title = "貼圖資訊"
        # sticker_name = discord.ui.TextInput(label="貼圖名稱", placeholder="貼圖名稱", required=True)
        # sticker_idx = discord.ui.TextInput(label="貼圖編號", placeholder="貼圖編號", required=True)
        # link = discord.ui.TextInput(label="連結(這個改了也沒用 只是給你去找貼圖的)", default="https://store.line.me/home/zh-Hant")
        sticker_id = ""
        
        async def on_submit(self, interaction: discord.Interaction, /) -> None:
            sticker_json = requests.get("https://stickershop.line-scdn.net/stickershop/v1/product/{}/iphone/productInfo.meta".format(self.sticker_id))
            sticker_json_format = json.loads(sticker_json.text)
            
            select_view = LineSticker.StickerSelectView(sticker_json_format)
            await interaction.response.send_message(view=select_view, ephemeral=True)

    class EmojiModal(discord.ui.Modal, title="表情貼資訊"):
        title = "表情貼資訊"
        sticker_name = discord.ui.TextInput(label="表情貼名稱", placeholder="表情貼名稱", required=True)
        sticker_idx = discord.ui.TextInput(label="表情貼編號", placeholder="表情貼編號", required=True)
        link = discord.ui.TextInput(label="連結(這個改了也沒用 只是給你去找貼圖的)", default="https://store.line.me/home/zh-Hant")
    
        async def on_submit(self, interaction: discord.Interaction, /) -> None:
            # Modal submits must be acknowledged within 3 seconds.
            if not interaction.response.is_done():
                await interaction.response.defer(thinking=True)
            
            if "emojiID=" not in self.sticker_name.value:
                url = "https://store.line.me/api/search/emoji?query={}&offset=0&limit=1&type=ALL&includeFacets=false".format(self.sticker_name.value)
                url = quote(url, safe='/:?=&')
                
                cmd = "curl -s --location --request GET '{}' --header 'Accept-Language:zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ko;q=0.6;Cookie: display_lang=zh-Hant;'".format(url)
                response = os.popen(cmd).read()
                res_json = json.loads(response)
            
                emoji_json = requests.get("https://stickershop.line-scdn.net/sticonshop/v1/sticon/{}/iphone/meta.json".format(res_json['items'][0]['id']))
                emoji_json_format = json.loads(emoji_json.text)
                emoji_pack_id = res_json['items'][0]['id']
                print(emoji_json_format)

                if "sticonResourceType" in emoji_json_format.keys():
                    await self.animate(emoji_json_format, emoji_pack_id, interaction)
                    return
                
                real_sticker_id = emoji_json_format['orders'][int(self.sticker_idx.value) - 1]
                real_sticker_png = requests.get("https://stickershop.line-scdn.net/sticonshop/v1/sticon/{}/iPhone/{}.png".format(res_json['items'][0]['id'], real_sticker_id), stream=True)
                arr = io.BytesIO(real_sticker_png.content)
                arr.seek(0)
                file = discord.File(arr)
                file.filename = "file.png"
                await interaction.followup.send(file=file)
            else:            
                emoji_json = requests.get("https://stickershop.line-scdn.net/sticonshop/v1/sticon/{}/iphone/meta.json".format(self.sticker_name.value.split("=")[1]))
                emoji_json_format = json.loads(emoji_json.text)
                print(emoji_json_format)

                if "sticonResourceType" in emoji_json_format.keys():
                    await self.animate(emoji_json_format, self.sticker_name.value.split("=")[1],interaction)
                    return
                
                real_sticker_id = emoji_json_format['orders'][int(self.sticker_idx.value) - 1]
                real_sticker_png = requests.get("https://stickershop.line-scdn.net/sticonshop/v1/sticon/{}/iPhone/{}.png".format(self.sticker_name.value.split("=")[1], real_sticker_id), stream=True)
                arr = io.BytesIO(real_sticker_png.content)
                arr.seek(0)
                file = discord.File(arr)
                file.filename = "file.png"
                await interaction.followup.send(file=file)

        async def animate(self, emoji_json_format, emoji_pack_id, interaction:discord.Interaction):
            real_sticker_id = emoji_json_format['orders'][int(self.sticker_idx.value) - 1]
            # https://stickershop.line-scdn.net/sticonshop/v1/sticon/6124aa4ae72c607c18108562/iPhone/039_animation.png?v=3
            real_sticker_png = requests.get("https://stickershop.line-scdn.net/sticonshop/v1/sticon/{}/iPhone/{}_animation.png".format(emoji_pack_id, real_sticker_id), stream=True)
            arr = io.BytesIO(real_sticker_png.content)
            arr.seek(0)
            
            ori_apng = Image.open(arr)
            ori_apng_arr = []
            new_apng_arr = []

            for i in range(ori_apng.n_frames):
                ori_apng.seek(i)
                print(ori_apng.tell())
                ori_apng_arr.append(ori_apng.copy())

            for png in ori_apng_arr:
                new_apng_arr.append(png.convert("RGBA"))

            # output = io.BytesIO()
            # ori_apng.save(output, format="GIF",save_all=True)
            new_apng_arr[0].save("test-{}.gif".format(real_sticker_id),save_all=True,disposal=2, append_images=new_apng_arr[1:],loop=0)
            output_gif = open("test-{}.gif".format(real_sticker_id), "rb")
            file = discord.File(output_gif)
            file.filename = "file.gif"
            await interaction.followup.send(file=file)
            output_gif.close()
            os.remove("test-{}.gif".format(real_sticker_id))

    class WhateverSticker(discord.ui.Modal, title="Line隨你填貼圖"):
        title = "貼圖資訊"
        sticker_name = discord.ui.TextInput(label="貼圖名稱", placeholder="貼圖名稱", required=True)
        sticker_idx = discord.ui.TextInput(label="貼圖編號", placeholder="貼圖編號", required=True)
        sticker_input = discord.ui.TextInput(label="隨你填", placeholder="隨你填", required=True)
        link = discord.ui.TextInput(label="連結(這個改了也沒用 只是給你去找貼圖的)", default="https://store.line.me/home/zh-Hant")
        
        async def on_submit(self, interaction: discord.Interaction, /) -> None:
            url = "https://store.line.me/api/search/sticker?query={}&offset=0&limit=200&type=ALL&includeFacets=false".format(self.sticker_name.value)
            url = quote(url, safe='/:?=&')
            
            cmd = "curl -s --location --request GET '{}' --header 'Accept-Language:zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ko;q=0.6;Cookie: display_lang=zh-Hant;'".format(url)
            k = os.popen(cmd)
            response = k.read()
            # print(response)
            res_json = json.loads(response)
            res_json['items'] = list(filter(lambda x:x['stickerResourceType'] == "NAME_TEXT", res_json['items']))
            print(json.dumps(res_json, indent=4))
            # https://store.line.me/api/custom-sticker/preview/14332/zh-Hant?text=plp
            header = {
                "Cookie": "oa=FRIEND; uu=r38SvzdvqKjM3tuVjijKqwb3pKtHKwtVt2efGtqbfn8uSykiOltewliroXBeccbr; display_lang=zh-Hant; ss=jsHkHdoh9o7MUHGTHsTdHVd0MXl2FiEA9YMLC2kOKtZTAPQYbg7uHidi87JGx5TKkWs6gthxc66QJJcWYq3XbGMIvcV8PSyyeSCP:1af9a7:18e73ab4e92",
                "x-requested-with": "XMLHttpRequest"
            }
            sticker_json = requests.get("https://store.line.me/api/custom-sticker/preview/{}/zh-Hant?text={}&_={}".format(res_json['items'][0]['id'], self.sticker_input.value,calendar.timegm(datetime.datetime.utcnow().utctimetuple())), headers=header)
            # print(sticker_json)
            sticker_json_format = json.loads(sticker_json.text)
            # print(sticker_json_format)
            
            base = sticker_json_format['stickerPayloads'][int(self.sticker_idx.value) - 1]['customBaseUrl']
            text = sticker_json_format['stickerPayloads'][int(self.sticker_idx.value) - 1]['customOverlayUrl']
            base_png = requests.get(base, stream=True)
            text_png = requests.get(text, stream=True)

            base_arr = io.BytesIO(base_png.content)
            text_arr = io.BytesIO(text_png.content)
            base_arr.seek(0)
            text_arr.seek(0)

            base_png_pil = Image.open(base_arr)
            text_png_pil = Image.open(text_arr)
            
            base_png_pil.paste(text_png_pil, (0, 0), text_png_pil)
            output = io.BytesIO()
            base_png_pil.save(output, format="PNG")
            output.seek(0)
            file = discord.File(output)
            file.filename = "file.png"
            await interaction.response.send_message(file=file)


            # arr = io.BytesIO(real_sticker_png.content)
            # arr.seek(0)
            # file = discord.File(arr)
            # file.filename = "file.png"
            # await interaction.response.send_message(file=file)
            # k.close()

            
    class MessageSticker(discord.ui.Modal, title="訊息貼圖"):
        title = "貼圖資訊"
        sticker_name = discord.ui.TextInput(label="貼圖名稱", placeholder="貼圖名稱", required=True)
        sticker_idx = discord.ui.TextInput(label="貼圖編號", placeholder="貼圖編號", required=True)
        sticker_input = discord.ui.TextInput(label="訊息", placeholder="訊息",style=discord.TextStyle.paragraph, required=True)
        link = discord.ui.TextInput(label="連結(這個改了也沒用 只是給你去找貼圖的)", default="https://store.line.me/home/zh-Hant")

        async def on_submit(self, interaction: discord.Interaction, /) -> None:
            url = "https://store.line.me/api/search/sticker?query={}&offset=0&limit=200&type=ALL&includeFacets=false".format(self.sticker_name.value)
            url = quote(url, safe='/:?=&')
            
            cmd = "curl -s --location --request GET '{}' --header 'Accept-Language:zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ko;q=0.6;Cookie: display_lang=zh-Hant;'".format(url)
            k = os.popen(cmd)
            response = k.read()
            res_json = json.loads(response)
            res_json['items'] = list(filter(lambda x:x['stickerResourceType'] == "PER_STICKER_TEXT", res_json['items']))
            # https://store.line.me/api/custom-sticker/preview/14332/zh-Hant?text=plp
            header = {
                "Cookie": "uu=wlTjdMwOfiD0OvAniUcSKhbRWpMhoWywCGPFXyKnjRgEZZI4Neg2bShSea8jcyHp; ss=wvkNkyeqW3BsQdfyJ7450HCUilzKJEhEB7DNdAScjBdlxzeVWWu5OwCsNNeevu86LQufVbjW0v5AC0mSXRuPfN4FlCjvr2nVNnUR:1286d8:187c0d9ffea; display_lang=zh-Hant;",
                "x-requested-with": "XMLHttpRequest"
            }

            sticker_json = requests.get("https://stickershop.line-scdn.net/stickershop/v1/product/{}/iphone/productInfo.meta".format(res_json['items'][0]['id']))
            sticker_json_format = json.loads(sticker_json.text)


            real_sticker_id = sticker_json_format['stickers'][int(self.sticker_idx.value) - 1]['id']

            header = {
                "referer": "https://store.line.me/stickershop/product/{}/zh-Hant".format(res_json['items'][0]['id']),
            }

            # 訊息貼圖
            # https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iPhone/base/plus/sticker@2x.png
            # https://store.line.me/overlay/sticker/{}/{}/iPhone/sticker.png?text={}
            # 需要referer https://store.line.me/stickershop/product/{}/zh-Hant

            base = requests.get("https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iPhone/base/plus/sticker@2x.png".format(real_sticker_id))
            text = requests.get("https://store.line.me/overlay/sticker/{}/{}/iPhone/sticker.png?text={}".format(res_json['items'][0]['id'], real_sticker_id, self.sticker_input.value), headers=header)

            base_arr = io.BytesIO(base.content)
            text_arr = io.BytesIO(text.content)

            base_arr.seek(0)
            text_arr.seek(0)

            base_png_pil = Image.open(base_arr)
            base_png_pil = base_png_pil.convert("RGBA")
            text_png_pil = Image.open(text_arr)
            text_png_pil = text_png_pil.convert("RGBA")
            # text_png_pil.save("test.png")

            # base_png_pil.paste(text_png_pil, (0, 0), text_png_pil)
            base_png_pil = Image.alpha_composite(base_png_pil, text_png_pil)

            output = io.BytesIO()
            base_png_pil.save(output, format="PNG")
            output.seek(0)
            file = discord.File(output)
            file.filename = "file.png"
            await interaction.response.send_message(file=file)
            
    class StickerOutputModal(discord.ui.Modal, title="貼圖資訊"):
        title = "貼圖資訊"
        sticker_name = discord.ui.TextInput(label="貼圖ID", placeholder="貼圖ID", required=True)
        # channel_id = discord.ui.TextInput(label="頻道ID", placeholder="頻道ID", required=True)
        # sticker_idx = discord.ui.TextInput(label="貼圖編號", placeholder="貼圖編號", required=True)
        link = discord.ui.TextInput(label="連結(這個改了也沒用 只是給你去找貼圖的)", default="https://store.line.me/home/zh-Hant")
        
        def __init__(self, channel):
            self.channel_id = channel
            super().__init__()
                      
        async def on_submit(self, interaction: discord.Interaction, /) -> None:
            if interaction.guild is None:
                return await interaction.response.send_message("請在伺服器內使用")
            channel = interaction.guild.get_channel(int(self.channel_id))
            
            sticker_json = requests.get("https://stickershop.line-scdn.net/stickershop/v1/product/{}/iphone/productInfo.meta".format(self.sticker_name.value))
            # print(sticker_json.text)
            sticker_json_format = json.loads(sticker_json.text)
            
            title_msg = ""
            
            if "zh-Hant" in sticker_json_format["title"].keys():
                title_msg = sticker_json_format["title"]["zh-Hant"]
            elif "ja" in sticker_json_format["title"].keys():
                title_msg = sticker_json_format["title"]["ja"]
            else:
                title_msg = sticker_json_format["title"]["en"]
            await interaction.response.send_message("擷取中，請稍後，請到指定的論壇頻道查看", ephemeral=True)
            
            
            thread, _ = await channel.create_thread(name="{}".format(title_msg), content="貼圖擷取-{}".format(title_msg))
            await thread.send("# 貼圖資訊\n貼圖名稱: {}\n貼圖ID: {}".format(title_msg, self.sticker_name.value))
            print(len(sticker_json_format['stickers']))
            if 'hasAnimation' in sticker_json_format:
                if sticker_json_format['hasAnimation']:
                    for idx, i in enumerate(sticker_json_format['stickers']):
                        print(i["id"])
                        await self.animate(idx, i["id"], thread)
                        await wait()
                    
                    # await self.animate(sticker_json_format, interaction)
                    # await interaction.response.send_message("暫不支援動態貼圖")
                    return

            
            for idx, i in enumerate(sticker_json_format['stickers']):
                real_sticker_id = i['id']
                real_sticker_png = requests.get("https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iphone/sticker@2x.png".format(real_sticker_id), stream=True)
                arr = io.BytesIO(real_sticker_png.content)
                arr.seek(0)
                file = discord.File(arr)
                file.filename = "file.png"
                # await interaction.response.send_message(content="{}".format(idx),file=file)
                await thread.send(content="{}".format(idx+1),file=file)
                await wait()
            
        async def animate(self, idx, real_sticker_id, thread: discord.Thread):
            # real_sticker_id = sticker_json_format['stickers'][int(self.sticker_idx.value) - 1]['id']
            real_sticker_png = requests.get("https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iPhone/sticker_animation@2x.png".format(real_sticker_id), stream=True)
            arr = io.BytesIO(real_sticker_png.content)
            arr.seek(0)
            
            ori_apng = Image.open(arr)
            ori_apng_arr = []
            new_apng_arr:list[Image.Image] = []

            for i in range(ori_apng.n_frames):
                ori_apng.seek(i)
                print(ori_apng.tell())
                ori_apng_arr.append(ori_apng.copy())

            for png in ori_apng_arr:
                new_apng_arr.append(png.convert("RGBA"))
            # output = io.BytesIO()
            # ori_apng.save(output, format="GIF",save_all=True)
            new_apng_arr[0].save("sticker-{}.gif".format(real_sticker_id),save_all=True,disposal=2, append_images=new_apng_arr[1:],loop=0)
            output_gif = open("sticker-{}.gif".format(real_sticker_id), "rb")
            file = discord.File(output_gif)
            file.filename = "file.gif"
            await thread.send(content="{}".format(idx+1),file=file)
            output_gif.close()
            os.remove("sticker-{}.gif".format(real_sticker_id))
            
            
    class SoundSticker():
        pass
    # 搜尋貼圖API 
    # API search sticker
    # GET https://store.line.me/api/search/sticker
    # query 搜尋字串
    # offset 從第幾個開始傳資料
    # limit 總共傳幾筆資料 上限1001
    # type (? 不太確定 反正先設定ALL)
    # includeFacets (? false)
            
    # 拿貼圖資料
    # https://stickershop.line-scdn.net/stickershop/v1/product/10226950/LINEStorePC/productInfo.meta
    
    # 拿貼圖網址
    # https://stickershop.line-scdn.net/stickershop/v1/sticker/{id}/iphone/sticker@2x.png
    
    # 動態貼圖 格式APNG 須轉換成GIF
    # https://stickershop.line-scdn.net/stickershop/v1/sticker/{id}/iPhone/sticker_animation@2x.png

    # 隨你填
    # https://stickershop.line-scdn.net/stickershop/v1/sticker/{id}/iPhone/base/sticker@2x.png

    # 訊息貼圖
    # https://stickershop.line-scdn.net/stickershop/v1/sticker/{}/iPhone/base/plus/sticker@2x.png
    # https://store.line.me/overlay/sticker/14473251/{}/iPhone/sticker.png?text={}
    # 需要referer https://store.line.me/stickershop/product/{}/zh-Hant
        
    # 表情貼
    # metadata https://stickershop.line-scdn.net/sticonshop/v1/{ID}/sticon/iPhone/meta.json
    # 靜態 https://stickershop.line-scdn.net/sticonshop/v1/{ID}/sticon/iPhone/{number}.png
    # 動態 https://stickershop.line-scdn.net/sticonshop/v1/{ID}/sticon/iPhone/{number}_animation.png
    
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.rename(search_text="搜尋字串", sticker_id="貼圖id")
    @app_commands.describe(search_text="搜尋字串", sticker_id="貼圖id")
    @commands.hybrid_command(name="line貼圖", description="搜尋字串與貼圖ID請擇一輸入", with_app_command=True)
    # @app_commands.guilds(utcs, hpsh)
    async def line貼圖(self, ctx: commands.Context, search_text: str = "", sticker_id:str = "") -> None:
        if search_text == "" and sticker_id == "":
            await ctx.send("請輸入搜尋字串或貼圖ID")
            return
        elif search_text != "" and sticker_id != "":
            await ctx.send("搜尋字串與貼圖ID同時存在，請擇一輸入")
            return

        # Slash/hybrid invocations must be acknowledged quickly.
        if ctx.interaction is not None and not ctx.interaction.response.is_done():
            await ctx.interaction.response.defer(thinking=True)

        # If sticker_id is provided, skip search and show that pack directly.
        if sticker_id != "":
            product_url = (
                "https://stickershop.line-scdn.net/stickershop/v1/product/{}/iphone/productInfo.meta".format(
                    sticker_id
                )
            )
            try:
                sticker_json_text = await asyncio.to_thread(
                    lambda: requests.get(product_url, timeout=15).text
                )
                sticker_json_format = json.loads(sticker_json_text)
            except Exception:
                return await ctx.send("取得貼圖資訊失敗，請稍後再試。")

            select_view = LineSticker.StickerSelectView(sticker_json_format)
            if ctx.interaction is not None:
                await ctx.interaction.followup.send(view=select_view, ephemeral=True)
            else:
                await ctx.send(view=select_view)
            return
        
        
        url = "https://store.line.me/api/search/sticker?query={}&offset=0&limit=20&type=ALL&includeFacets=false".format(search_text)
        url = quote(url, safe='/:?=&')
        
        cmd = "curl -s --location --request GET '{}' --header 'Accept-Language:zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ko;q=0.6;Cookie: display_lang=zh-Hant;'".format(url)
        k = os.popen(cmd)
        response = k.read()
        res_json = json.loads(response)
        
        # res_json['items'][0]
        
        selection = discord.ui.Select(placeholder="請選擇貼圖")
        
        view = discord.ui.View()
        view.add_item(selection)
        
        for i in res_json['items']:
            selection.add_option(label=i['title'], value=i['id'])
            
        async def selection_callback(interaction: discord.Interaction):
            # Component interactions must be acknowledged quickly (<=3s).
            # The LINE API fetch can be slow and `requests` is blocking, so defer first.
            await interaction.response.defer(ephemeral=True, thinking=True)

            product_id = interaction.data["values"][0]
            product_url = (
                "https://stickershop.line-scdn.net/stickershop/v1/product/{}/iphone/productInfo.meta".format(
                    product_id
                )
            )

            try:
                sticker_json_text = await asyncio.to_thread(
                    lambda: requests.get(product_url, timeout=15).text
                )
                sticker_json_format = json.loads(sticker_json_text)
            except Exception:
                return await interaction.followup.send(
                    "取得貼圖資訊失敗，請稍後再試。", ephemeral=True
                )

            select_view = LineSticker.StickerSelectView(sticker_json_format)
            await interaction.followup.send(view=select_view, ephemeral=True)

            # Keep the original select menu message intact.
            try:
                await interaction.message.edit(content="請選擇貼圖", view=view)
            except Exception:
                pass
        
        selection.callback = selection_callback
        
        
        
        
        await ctx.send("請選擇貼圖", view=view)
        
        # sticker = self.StickerModal()
        # if ctx.interaction is not None:
        #     await ctx.interaction.response.send_modal(sticker)
        
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="line表情貼", description="line表情貼 限制：動態待測", with_app_command=True)
    # @app_commands.guilds(utcs, hpsh)
    async def line表情貼(self, ctx: commands.Context) -> None:
        sticker = self.EmojiModal()
        if ctx.interaction is not None:
            await ctx.interaction.response.send_modal(sticker)
    
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="line隨你填", description="line隨你填 限制：動態待測", with_app_command=True)
    # @app_commands.guilds(utcs, hpsh)
    async def line隨你填(self, ctx: commands.Context) -> None:
        sticker = self.WhateverSticker()
        if ctx.interaction is not None:
            await ctx.interaction.response.send_modal(sticker)

    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @commands.hybrid_command(name="line訊息貼圖", description="line訊息貼圖 限制：動態待測", with_app_command=True)
    # @app_commands.guilds(utcs, hpsh)
    async def line訊息貼圖(self, ctx: commands.Context) -> None:
        sticker = self.MessageSticker()
        if ctx.interaction is not None:
            await ctx.interaction.response.send_modal(sticker)
            
    @commands.hybrid_command(name="line貼圖輸出", description="建議用在討論串")
    @app_commands.guilds(utcs, hpsh)
    async def line貼圖輸出(self, ctx: commands.Context) -> None:
        
        # filter 
        forum_channels = ctx.guild.channels
        # for c in forum_channels:
        #     print(c.name, c.type == discord.ChannelType.forum)
            
        forum_channels = list(filter(lambda c: c.type == discord.ChannelType.forum, forum_channels))
        forum_channels = list(filter(lambda c: c.permissions_for(ctx.author).view_channel, forum_channels))
        # print(forum_channels)
        selection = discord.ui.Select(placeholder="請選擇頻道", min_values=1, max_values=1)
        for c in forum_channels:
            selection.add_option(label=c.name, value=str(c.id))
            
        async def selection_callback(interaction: discord.Interaction):
            sticker = self.StickerOutputModal(interaction.data["values"][0])
            await interaction.response.send_modal(sticker)
        
        selection.callback = selection_callback    
        
        view = discord.ui.View()
        view.add_item(selection)
        await ctx.send("請選擇輸出頻道", view=view, ephemeral=True)
        
        
        
        # sticker = self.StickerOutputModal()
        # if ctx.interaction is not None:
        #     await ctx.interaction.response.send_modal(sticker)

async def wait():
    await asyncio.sleep(0.3)
    # print('I waited 5 seconds')

        
async def setup(bot: commands.Bot):
    await bot.add_cog(LineSticker(bot))