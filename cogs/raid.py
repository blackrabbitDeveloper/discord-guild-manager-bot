from dataclasses import dataclass, field

import discord
from discord import app_commands
from discord.ext import commands


@dataclass
class PartyData:
    activity: str
    max_members: int
    creator_id: int
    description: str = ""
    participants: list[int] = field(default_factory=list)
    waitlist: list[int] = field(default_factory=list)

    def add_member(self, user_id: int) -> str:
        if user_id in self.participants or user_id in self.waitlist:
            return "already_joined"
        if len(self.participants) < self.max_members:
            self.participants.append(user_id)
            return "joined"
        self.waitlist.append(user_id)
        return "waitlisted"

    def remove_member(self, user_id: int) -> int | None:
        if user_id in self.participants:
            self.participants.remove(user_id)
            if self.waitlist:
                promoted = self.waitlist.pop(0)
                self.participants.append(promoted)
                return promoted
            return None
        if user_id in self.waitlist:
            self.waitlist.remove(user_id)
        return None


class Party(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.parties: dict[int, PartyData] = {}  # message_id -> PartyData

    def _build_embed(self, party: PartyData) -> discord.Embed:
        embed = discord.Embed(
            title=f"⚔️ 파티 모집: {party.activity}",
            color=discord.Color.red(),
        )

        if party.description:
            embed.add_field(name="📝 내용", value=party.description, inline=False)

        embed.add_field(
            name="모집 인원",
            value=f"{len(party.participants)}/{party.max_members}",
            inline=False,
        )

        if party.participants:
            participants_text = "\n".join(f"<@{uid}>" for uid in party.participants)
        else:
            participants_text = "없음"
        embed.add_field(name="참가자", value=participants_text, inline=False)

        if party.waitlist:
            waitlist_text = "\n".join(
                f"{i+1}. <@{uid}>" for i, uid in enumerate(party.waitlist)
            )
            embed.add_field(name="대기열", value=waitlist_text, inline=False)

        return embed

    @app_commands.command(name="파티모집", description="파티 모집을 시작합니다")
    @app_commands.describe(활동="활동 이름", 인원="모집 인원 수", 내용="추가 설명 (선택)")
    async def party(self, interaction: discord.Interaction, 활동: str, 인원: int, 내용: str = ""):
        if 인원 < 1 or 인원 > 50:
            await interaction.response.send_message(
                "❌ 인원은 1~50 사이로 입력해주세요.", ephemeral=True
            )
            return

        party_data = PartyData(
            activity=활동, max_members=인원, creator_id=interaction.user.id, description=내용
        )
        embed = self._build_embed(party_data)
        embed.set_footer(text=f"모집자: {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("✅")
        self.parties[msg.id] = party_data

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        if str(payload.emoji) != "✅":
            return
        if payload.message_id not in self.parties:
            return

        party = self.parties[payload.message_id]
        result = party.add_member(payload.user_id)

        channel = self.bot.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        if result == "already_joined":
            return

        embed = self._build_embed(party)
        embed.set_footer(text=msg.embeds[0].footer.text)
        await msg.edit(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "✅":
            return
        if payload.message_id not in self.parties:
            return

        party = self.parties[payload.message_id]
        promoted = party.remove_member(payload.user_id)

        channel = self.bot.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        embed = self._build_embed(party)
        embed.set_footer(text=msg.embeds[0].footer.text)
        await msg.edit(embed=embed)

        if promoted:
            await channel.send(f"<@{promoted}> 님이 대기열에서 참가자로 승격되었습니다! ⚔️")


async def setup(bot: commands.Bot):
    await bot.add_cog(Party(bot))
