# discord_bot.py
import json
import os
from pathlib import Path

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from msu_market import compute_price_stats, fetch_items, format_price_table

load_dotenv()

DATA_FILE = Path("tracked_items.json")
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def load_tracked_items():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_tracked_items(items):
    with open(DATA_FILE, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


tracked_items = load_tracked_items()


@bot.event
async def on_ready():
    print(f"Bot已上線，登入為 {bot.user}")
    check_items.start()
    print(f"定時查詢開啟，時間間隔為{os.getenv("CHECK_INTERVAL")}秒。")


@bot.command(name="add")
async def add_item(ctx, *, item_name: str):
    item_name = item_name.strip().lower()
    if item_name in tracked_items:
        await ctx.send(f"'{item_name}' 已在追蹤清單中。")
        return
    tracked_items.append(item_name)
    save_tracked_items(tracked_items)
    await ctx.send(f"已將 '{item_name}' 加入追蹤清單。")


@bot.command(name="remove")
async def remove_item(ctx, *, item_name: str):
    item_name = item_name.strip().lower()
    if item_name not in tracked_items:
        await ctx.send(f"清單中沒有 '{item_name}'。")
        return
    tracked_items.remove(item_name)
    save_tracked_items(tracked_items)
    await ctx.send(f"已將 '{item_name}' 從追蹤清單中移除。")


@bot.command(name="list")
async def list_items(ctx):
    if not tracked_items:
        await ctx.send("目前沒有追蹤任何裝備。")
    else:
        await ctx.send("目前追蹤的裝備有:\n" + "\n".join(tracked_items))


@bot.command(name="price")
async def fetch_price(ctx, *, item_name: str):
    try:
        data = fetch_items(item_name)
    except Exception as e:
        await ctx.send("查詢時發生問題，請稍後再試。")
        print(e)
        return

    items = data.get("items", [])
    if not items:
        await ctx.send("未查詢到任何道具。")
        return

    stats = compute_price_stats(items)
    if not stats:
        await ctx.send("沒有找到任何價格資訊。")
        return

    table_str = format_price_table(stats)
    await ctx.send(table_str)


@tasks.loop(seconds=os.getenv("CHECK_INTERVAL"))
async def check_items():
    # 定期檢查追蹤的裝備，並在指定頻道回報
    channel = await bot.fetch_channel(os.getenv("REPORT_CHANNEL_ID"))

    if channel is None:
        print("指定的報告頻道不存在或Bot沒有存取權限。")
        return
    if not tracked_items:
        # 沒有裝備就不報告
        return
    # 查詢每個裝備並發佈結果
    msg_parts = []
    for item_name in tracked_items:
        try:
            data = fetch_items(item_name)
            items = data.get("items", [])
            stats = compute_price_stats(items)
            msg_parts.append(format_price_table(item_name, stats))
        except Exception as e:
            msg_parts.append(f"**{item_name}**\n查詢發生錯誤: {e}")

    # 將結果分批發送
    # 若單次消息過長, 可再優化分批策略
    report_msg = "\n\n".join(msg_parts)
    await channel.send(report_msg)


bot.run(os.getenv("BOT_TOKEN"))
