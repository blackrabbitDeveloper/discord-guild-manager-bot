import discord
from discord import app_commands
from discord.ext import commands


class Clear(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="clear", description="채널 메시지를 일괄 삭제합니다")
    @app_commands.describe(amount="삭제할 메시지 수 (1~100)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message(
                "❌ 1~100 사이의 숫자를 입력해주세요.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(
            f"✅ {len(deleted)}개 메시지를 삭제했습니다.", ephemeral=True
        )

    @clear.error
    async def clear_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ 메시지 관리 권한이 필요합니다.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Clear(bot))
