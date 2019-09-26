DiscordBotUTCS
===

## 第一次使用就上手

這是一個可以用在111級資訊科學系Discord群組的聊天機器人
雖然目前功能不多，但透過大家的集思廣益，一定會讓他變得很厲害的

如果想要一起幫忙的話

1. 安裝Github Desktop
2. 找到這個Git專案的網址，到Github Desktop裡面貼上並clone到自己的電腦上
3. Clone完成後，在上方Current Branch選擇beta_master
4. 開始工作!
5. 工作完成後，到Github Desktop上的左下角Commit Change，然後點上面push到Github上
6. **我會先把程式碼clone下來，確認沒問題我就會Deploy到Bot上讓Bot執行**

基礎格式
---

```python=
每個指令應該需要的程式碼:(e.g. $laugh,$dance)

@bot.command()
    async def 變數名(ctx,變數...):
        #這裡做你要做的事
        await ctx.send()#裡面放要讓Bot講的東西
                  
```
>用這個讓機器人可以對特定的指令回應

## 以下待編輯
