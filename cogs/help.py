import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="봇 명령어 목록을 확인합니다")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 명령어 목록",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="/파티모집 활동:<이름> 인원:<숫자> [내용:<설명>]",
            value="파티 모집을 시작합니다. ✅ 반응으로 참가/대기열 관리",
            inline=False,
        )
        embed.add_field(
            name="/clear amount:<숫자>",
            value="채널 메시지를 일괄 삭제합니다 (1~100개, 관리자 전용)",
            inline=False,
        )
        embed.add_field(
            name="/스케줄 내용 시간 채널 [멘션] [사전알림]",
            value="일회성 스케줄을 등록합니다 (관리자 전용)",
            inline=False,
        )
        embed.add_field(
            name="/스케줄반복 내용 요일 시간 채널 [멘션] [사전알림]",
            value="매주 반복 스케줄을 등록합니다 (관리자 전용)",
            inline=False,
        )
        embed.add_field(
            name="/스케줄목록",
            value="등록된 스케줄 목록을 확인합니다 (관리자 전용)",
            inline=False,
        )
        embed.add_field(
            name="/스케줄취소 번호:<ID>",
            value="등록된 스케줄을 취소합니다 (관리자 전용)",
            inline=False,
        )
        embed.add_field(
            name="/주사위 [최대값]",
            value="주사위 굴리기 (기본 1~100, 버튼으로 참여/종료)",
            inline=False,
        )
        embed.add_field(
            name="/help",
            value="이 도움말을 표시합니다",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
