import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"봇 로그인: {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"슬래시 명령어 {len(synced)}개 동기화 완료")
    except Exception as e:
        print(f"명령어 동기화 실패: {e}")


async def load_cogs():
    await bot.load_extension("cogs.clear")
    await bot.load_extension("cogs.raid")
    await bot.load_extension("cogs.help")
    await bot.load_extension("cogs.schedule")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("BOT_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
