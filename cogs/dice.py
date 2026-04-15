import random

import discord
from discord import app_commands
from discord.ext import commands


class DiceView(discord.ui.View):
    def __init__(self, max_num: int, creator_id: int):
        super().__init__(timeout=None)
        self.max_num = max_num
        self.creator_id = creator_id
        self.results: dict[int, int] = {}  # user_id -> roll

    def _build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎲 주사위 (1~{self.max_num})",
            color=discord.Color.gold(),
        )

        if self.results:
            best_id = max(self.results, key=self.results.get)
            lines = []
            for uid, roll in self.results.items():
                crown = "  👑" if uid == best_id else ""
                lines.append(f"<@{uid}>: **{roll}**{crown}")
            embed.description = "\n".join(lines)
        else:
            embed.description = "아직 참여자가 없습니다."

        return embed

    def _build_final_embed(self) -> discord.Embed:
        embed = self._build_embed()
        embed.title = f"🎲 주사위 (1~{self.max_num}) — 종료됨"
        embed.color = discord.Color.greyple()
        return embed

    @discord.ui.button(label="🎲 참여", style=discord.ButtonStyle.primary)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.results:
            await interaction.response.send_message(
                "❌ 이미 참여했습니다.", ephemeral=True
            )
            return

        roll = random.randint(1, self.max_num)
        self.results[interaction.user.id] = roll
        embed = self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🛑 종료", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message(
                "❌ 개설자만 종료할 수 있습니다.", ephemeral=True
            )
            return

        for item in self.children:
            item.disabled = True

        embed = self._build_final_embed()
        await interaction.response.edit_message(embed=embed, view=self)

        if self.results:
            best_id = max(self.results, key=self.results.get)
            best_roll = self.results[best_id]
            await interaction.channel.send(
                f"🎉 축하합니다! <@{best_id}> 님이 **{best_roll}**점으로 1등입니다!"
            )

        self.stop()


class Dice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="주사위", description="주사위 굴리기를 시작합니다")
    @app_commands.describe(최대값="주사위 최대 숫자 (기본: 100)")
    async def dice(self, interaction: discord.Interaction, 최대값: int = 100):
        if 최대값 < 2:
            await interaction.response.send_message(
                "❌ 최대값은 2 이상이어야 합니다.", ephemeral=True
            )
            return

        view = DiceView(max_num=최대값, creator_id=interaction.user.id)
        embed = view._build_embed()
        embed.set_footer(text=f"개설자: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Dice(bot))
