import discord
from discord.ext import commands
import re
class AffectionCog(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
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
        match = self.bot.config.AFFECTION_DEBUG.match(content)
        if match:
            uid = match.group(2)
            target = message.guild.get_member(int(uid))
            if target is None: return
            await message.reply(f"我对{target.mention}的好感值是{self.bot.db.affection_lookup_or_init(uid)}")
        return
async def setup(bot):
    await bot.add_cog(AffectionCog(bot))
