import discord
import re
from discord.ext import commands
from datetime import datetime,timezone,timedelta
class ManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self,message):
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
        noble_match = self.bot.config.NOBILITY_PATTERN.match(content)
        if noble_match:
            HKT = timezone(timedelta(hours = 8))
            time_str = datetime.now(HKT).strftime("%Y-%m-%d")
            title = noble_match.group(3).strip()
            uid = noble_match.group(2)
            target = message.guild.get_member(int(uid))
            if target is None:
                await message.reply("所指非人。")
                return
            if message.author.id != self.bot.config.OWNER_ID:
                await message.reply("僭号裂土，罪该万死。")
                return
            granted_by = message.author.id
            if not title:
                await message.reply("无所可封。")
                return
            edict = await self.bot.llm.generate_edict(edict_type = "noble", target = target.mention, position = title)
            self.bot.db.add_noble(uid, title, str(granted_by), time_str)
            await message.channel.send(f"**封{target.mention}诏**\n{edict}")
            return
        else:
            archive_match = self.bot.config.ARCHIVE_PATTERN.match(content)
            if archive_match:
                uid = archive_match.group(2)
                raw = archive_match.group(3)
                link_match = re.search(r"(https?://\S+)", raw)
                link = None
                if link_match:
                    link = link_match.group(1)
                    raw = re.sub(r"https?://\S+", "", raw).strip()
                keywords = await self.bot.llm.extract_keywords(raw)
                print(f"[DEBUG] 修史入库 - 原话: '{raw}' -> 提炼向量词: '{keywords}'")
                HKT = timezone(timedelta(hours = 8))
                time_str = datetime.now(HKT).strftime("%Y-%m-%d")
                target = message.guild.get_member(int(uid))
                if target is None:
                    await message.reply("所指非人。")
                    return
                if message.author.id != self.bot.config.OWNER_ID:
                    await message.reply("你无权纂史。")
                    return
                edict = await self.bot.llm.generate_edict(edict_type = "archive", target=target.mention, reason = raw)
                await self.bot.db.add_archive(uid, raw, keywords, link, time_str)
                await message.reply(f"**诏**\n{edict}")
                return
async def setup(bot):
    await bot.add_cog(ManagementCog(bot))