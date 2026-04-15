import json
import os
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

DATA_FILE = "schedules.json"
KST = timezone(timedelta(hours=9))

WEEKDAY_MAP = {
    "월": 0, "화": 1, "수": 2, "목": 3, "금": 4, "토": 5, "일": 6,
}


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_guild_data(data: dict, guild_id: str) -> dict:
    if guild_id not in data:
        data[guild_id] = {"next_id": 1, "schedules": []}
    return data[guild_id]


class Schedule(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_schedules.start()

    def cog_unload(self):
        self.check_schedules.cancel()

    @tasks.loop(seconds=30)
    async def check_schedules(self):
        now = datetime.now(KST)
        data = load_data()
        changed = False

        for guild_id, guild_data in data.items():
            to_remove = []

            for schedule in guild_data["schedules"]:
                # 사전 알림 체크
                if schedule.get("pre_alert_min") and not schedule.get("pre_alerted"):
                    alert_time = datetime.fromisoformat(schedule["datetime"]) - timedelta(
                        minutes=schedule["pre_alert_min"]
                    )
                    if now >= alert_time:
                        await self._send_alert(schedule, pre=True)
                        schedule["pre_alerted"] = True
                        changed = True

                # 정시 알림 체크
                schedule_time = datetime.fromisoformat(schedule["datetime"])
                if now >= schedule_time and not schedule.get("alerted"):
                    await self._send_alert(schedule, pre=False)
                    schedule["alerted"] = True
                    changed = True

                    if schedule["type"] == "once":
                        to_remove.append(schedule["id"])
                    elif schedule["type"] == "repeat":
                        # 다음 주로 갱신
                        next_time = schedule_time + timedelta(weeks=1)
                        schedule["datetime"] = next_time.isoformat()
                        schedule["alerted"] = False
                        schedule["pre_alerted"] = False

            guild_data["schedules"] = [
                s for s in guild_data["schedules"] if s["id"] not in to_remove
            ]
            if to_remove:
                changed = True

        if changed:
            save_data(data)

    @check_schedules.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    async def _send_alert(self, schedule: dict, pre: bool):
        channel = self.bot.get_channel(schedule["channel_id"])
        if not channel:
            return

        mention = schedule.get("mention", "")
        content = schedule["content"]

        if pre:
            minutes = schedule["pre_alert_min"]
            msg = f"⏰ **{minutes}분 후** {content}"
        else:
            msg = f"🔔 **{content}**"

        if mention:
            msg = f"{mention} {msg}"

        await channel.send(msg)

    @app_commands.command(name="스케줄", description="일회성 스케줄을 등록합니다")
    @app_commands.describe(
        내용="알림 내용",
        시간="날짜와 시간 (예: 2026-04-16 21:00)",
        채널="알림을 보낼 채널",
        멘션="멘션할 역할 (선택)",
        사전알림="N분 전 미리 알림 (선택)",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def schedule_once(
        self,
        interaction: discord.Interaction,
        내용: str,
        시간: str,
        채널: discord.TextChannel,
        멘션: discord.Role = None,
        사전알림: int = None,
    ):
        try:
            dt = datetime.strptime(시간, "%Y-%m-%d %H:%M").replace(tzinfo=KST)
        except ValueError:
            await interaction.response.send_message(
                "❌ 시간 형식이 올바르지 않습니다. 예: `2026-04-16 21:00`", ephemeral=True
            )
            return

        if dt <= datetime.now(KST):
            await interaction.response.send_message(
                "❌ 과거 시간은 등록할 수 없습니다.", ephemeral=True
            )
            return

        data = load_data()
        guild_data = get_guild_data(data, str(interaction.guild_id))
        schedule_id = guild_data["next_id"]
        guild_data["next_id"] += 1

        entry = {
            "id": schedule_id,
            "type": "once",
            "content": 내용,
            "datetime": dt.isoformat(),
            "channel_id": 채널.id,
            "mention": 멘션.mention if 멘션 else "",
            "pre_alert_min": 사전알림,
            "alerted": False,
            "pre_alerted": False,
        }
        guild_data["schedules"].append(entry)
        save_data(data)

        embed = discord.Embed(title="✅ 스케줄 등록 완료", color=discord.Color.green())
        embed.add_field(name="ID", value=str(schedule_id), inline=True)
        embed.add_field(name="내용", value=내용, inline=True)
        embed.add_field(name="시간", value=시간, inline=True)
        embed.add_field(name="채널", value=채널.mention, inline=True)
        if 멘션:
            embed.add_field(name="멘션", value=멘션.mention, inline=True)
        if 사전알림:
            embed.add_field(name="사전알림", value=f"{사전알림}분 전", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="스케줄반복", description="매주 반복 스케줄을 등록합니다")
    @app_commands.describe(
        내용="알림 내용",
        요일="요일 (월/화/수/목/금/토/일)",
        시간="시간 (예: 21:00)",
        채널="알림을 보낼 채널",
        멘션="멘션할 역할 (선택)",
        사전알림="N분 전 미리 알림 (선택)",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def schedule_repeat(
        self,
        interaction: discord.Interaction,
        내용: str,
        요일: str,
        시간: str,
        채널: discord.TextChannel,
        멘션: discord.Role = None,
        사전알림: int = None,
    ):
        if 요일 not in WEEKDAY_MAP:
            await interaction.response.send_message(
                "❌ 올바른 요일을 입력해주세요. (월/화/수/목/금/토/일)", ephemeral=True
            )
            return

        try:
            time_parts = datetime.strptime(시간, "%H:%M")
        except ValueError:
            await interaction.response.send_message(
                "❌ 시간 형식이 올바르지 않습니다. 예: `21:00`", ephemeral=True
            )
            return

        # 다음 해당 요일 계산
        now = datetime.now(KST)
        target_weekday = WEEKDAY_MAP[요일]
        days_ahead = target_weekday - now.weekday()
        if days_ahead < 0 or (days_ahead == 0 and now.hour * 60 + now.minute >= time_parts.hour * 60 + time_parts.minute):
            days_ahead += 7
        next_date = now + timedelta(days=days_ahead)
        dt = next_date.replace(
            hour=time_parts.hour, minute=time_parts.minute, second=0, microsecond=0
        )

        data = load_data()
        guild_data = get_guild_data(data, str(interaction.guild_id))
        schedule_id = guild_data["next_id"]
        guild_data["next_id"] += 1

        entry = {
            "id": schedule_id,
            "type": "repeat",
            "content": 내용,
            "weekday": 요일,
            "time": 시간,
            "datetime": dt.isoformat(),
            "channel_id": 채널.id,
            "mention": 멘션.mention if 멘션 else "",
            "pre_alert_min": 사전알림,
            "alerted": False,
            "pre_alerted": False,
        }
        guild_data["schedules"].append(entry)
        save_data(data)

        embed = discord.Embed(title="✅ 반복 스케줄 등록 완료", color=discord.Color.green())
        embed.add_field(name="ID", value=str(schedule_id), inline=True)
        embed.add_field(name="내용", value=내용, inline=True)
        embed.add_field(name="요일", value=f"매주 {요일}요일", inline=True)
        embed.add_field(name="시간", value=시간, inline=True)
        embed.add_field(name="채널", value=채널.mention, inline=True)
        if 멘션:
            embed.add_field(name="멘션", value=멘션.mention, inline=True)
        if 사전알림:
            embed.add_field(name="사전알림", value=f"{사전알림}분 전", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="스케줄목록", description="등록된 스케줄 목록을 확인합니다")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def schedule_list(self, interaction: discord.Interaction):
        data = load_data()
        guild_data = get_guild_data(data, str(interaction.guild_id))

        if not guild_data["schedules"]:
            await interaction.response.send_message(
                "📭 등록된 스케줄이 없습니다.", ephemeral=True
            )
            return

        embed = discord.Embed(title="📅 스케줄 목록", color=discord.Color.blue())

        for s in guild_data["schedules"]:
            if s["type"] == "once":
                dt = datetime.fromisoformat(s["datetime"])
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = f"매주 {s['weekday']}요일 {s['time']}"

            value = f"시간: {time_str}\n채널: <#{s['channel_id']}>"
            if s.get("mention"):
                value += f"\n멘션: {s['mention']}"
            if s.get("pre_alert_min"):
                value += f"\n사전알림: {s['pre_alert_min']}분 전"

            embed.add_field(
                name=f"[{s['id']}] {s['content']} ({'반복' if s['type'] == 'repeat' else '일회'})",
                value=value,
                inline=False,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="스케줄취소", description="등록된 스케줄을 취소합니다")
    @app_commands.describe(번호="취소할 스케줄 ID")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def schedule_cancel(self, interaction: discord.Interaction, 번호: int):
        data = load_data()
        guild_data = get_guild_data(data, str(interaction.guild_id))

        found = None
        for s in guild_data["schedules"]:
            if s["id"] == 번호:
                found = s
                break

        if not found:
            await interaction.response.send_message(
                f"❌ ID {번호}에 해당하는 스케줄이 없습니다.", ephemeral=True
            )
            return

        guild_data["schedules"].remove(found)
        save_data(data)

        await interaction.response.send_message(
            f"✅ 스케줄 [{번호}] **{found['content']}** 이(가) 취소되었습니다.", ephemeral=True
        )

    @schedule_once.error
    @schedule_repeat.error
    @schedule_list.error
    @schedule_cancel.error
    async def schedule_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ 서버 관리 권한이 필요합니다.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Schedule(bot))
