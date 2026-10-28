import discord
import re
from discord.ext import commands
from datetime import datetime,timezone,timedelta
class PunishmentCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.tone_map = {
                "笞责": "轻微训诫，语带轻蔑",
                "杖责": "较重训诫，冷峻",
                "徒刑": "严厉，居高临下",
                "流放": "决绝，不再多言",
                "斩首": "极冷，一字千钧",
            }
        self._self_bans: set[int] = set()
    def is_admin(self, member: discord.Member) -> bool:
        return (
            member.guild_permissions.administrator
            or any(r.id == self.bot.config.ADMIN_ROLE_ID for r in member.roles)
        )
    def parse_duration(self, amount, unit, default_value:int, default_unit:str):
        if amount is None:
            amount, unit = default_value, default_unit
        elif unit is None:
            unit = default_unit
        secs = int(amount) * self.bot.config.UNIT_SECONDS[unit]
        return secs, f"{amount}{unit}"
    @commands.Cog.listener()
    async def on_message(self,message:discord.Message):
        if message.author == self.bot.user:
            return
        if not message.content:
            return
        if message.channel.id != self.bot.config.TARGET_CHANNEL_ID:
            return
        content = message.content
        for m in (f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"):
            content = content.replace(m, "", 1)
        content = content.strip()
        punishment_match = self.bot.config.CMD_PATTERN.match(content)
        if punishment_match:
            action, uid, amount, unit = punishment_match.groups()
            if not self.is_admin(message.author):
                await message.reply("此令非尔所可出。")
                return

            target = message.guild.get_member(int(uid))
            if target is None or target == message.author:
                await message.reply("所指非人。")
                return
            try:
                match action:
                    case "笞":
                        secs, dur_orig = self.parse_duration(amount, unit, 60, "s")
                        secs = min(secs, 28*86400)
                        if secs <= 0:
                            await message.reply("刑期无效。")
                            return
                        await target.timeout(timedelta(seconds = secs), reason = f"by {message.author}")
                        actionsakiko = "笞责"
                    case "杖":
                        secs, dur_orig = self.parse_duration(amount, unit, 60, "m")
                        secs = min(secs, 28*86400)
                        if secs <= 0:
                            await message.reply("刑期无效。")
                            return
                        await target.timeout(timedelta(seconds = secs), reason = f"by {message.author}")
                        actionsakiko = "杖责"
                    case "徒":
                        secs, dur_orig = self.parse_duration(amount, unit, 1, "d")
                        secs = min(secs, 28*86400)
                        if secs <= 0:
                            await message.reply("刑期无效。")
                            return
                        await target.timeout(timedelta(seconds = secs), reason = f"by {message.author}")
                        actionsakiko = "徒刑"
                    case "流":
                        await target.kick(reason=f"by {message.author}")
                        actionsakiko, dur_orig = "流放", "逐出"
                    case "死":
                        self._self_bans.add(target.id)
                        try:
                            await target.ban(reason=f"by {message.author}", delete_message_days=0)
                        except discord.Forbidden:
                            self._self_bans.discard(target.id)
                            raise
                        actionsakiko, dur_orig = "斩首", "永久"
            except discord.Forbidden:
                await message.reply("我权限不够。")
                return
            edict = await self.bot.llm.generate_edict(edict_type = "punish", target = target.mention, action = actionsakiko, duration = dur_orig, executor = message.author.display_name, tone = self.tone_map.get(actionsakiko, ""))
            await message.channel.send(f"**诏**\n{edict}")
            return
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        if guild.id != self.bot.config.GUILD_ID:
            return
        channel = guild.get_channel(self.bot.config.TARGET_CHANNEL_ID)
        if channel is None:
            return
        if user.id in self._self_bans:
            self._self_bans.discard(user.id)
            return
        edict = await self.bot.llm.generate_edict(target=user.mention, edict_type="punish", action="斩首", duration="永久", executor="管理员（手动）", tone = self.tone_map.get("斩首", ""))
        await channel.send(f"**诏**\n{edict}")
        return
async def setup(bot):
    await bot.add_cog(PunishmentCog(bot))