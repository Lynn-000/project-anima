import discord
from discord.ext import commands
import base64
import time
import re
from collections import deque
import asyncio
class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.HISTORY: dict[int, deque] = {}
        self._last_reply_time: dict[int, float] = {}

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.author == self.bot.user:
            return
        if not message.content and not message.attachments:
            return
        if message.channel.id != self.bot.config.TARGET_CHANNEL_ID:
            return
        content = message.content
        for m in (f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"):
            content = content.replace(m, "", 1)
        bvmatch = re.search(r"(播放)\s+(?:https?://\S*)?BV([0-9A-Za-z]{10})", message.content)
        if self.bot.config.CMD_PATTERN.match(content) or self.bot.config.NOBILITY_PATTERN.match(content) or self.bot.config.ARCHIVE_PATTERN.match(content) or self.bot.config.CYCLE_PATTERN.match(content) or self.bot.config.AFFECTION_DEBUG.match(content) or self.bot.config.GIF_STORE_PATTERN.match(content) or bvmatch:
            return
        hist = self.HISTORY.setdefault(message.channel.id, deque(maxlen=10))
        hist_content = content
        image_b64 = None
        for attachment in message.attachments:
            if attachment.content_type.startswith("image/"):
                image_bytes = await attachment.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
                break
        if image_b64:
            hist_content += " [发送了一张图片]"
        hist.append({"role": "user", "content": f"[{message.author.display_name}] {hist_content}"})
        iscalled = (self.bot.user in message.mentions or any(x in message.content.lower() for x in self.bot.config.NICKNAMES))
        if not(iscalled or (image_b64 is not None)):
            now = time.time()
            last_time = self._last_reply_time.get(message.channel.id, 0)
            if now - last_time < self.bot.config.COOLDOWN_SECONDS:
                return
            self._last_reply_time[message.channel.id] = now
        else:
            self._last_reply_time[message.channel.id] = time.time()
        reply = await self.bot.llm.chat_reply(message, list(hist), iscalled, image_b64)
        aff_match = re.search(r"<affectionate>\s*([+-]?\d+)\s*</affectionate>", reply)
        if aff_match:
            change = int(aff_match.group(1))
            change = max(-10, min(10, change))
            self.bot.db.change_affection_rating(message.author.id, change)
        reply = re.sub(r"<affectionate>.*?</affectionate>", "", reply).strip()
        gif_match = re.search(r"<gif>(.*?)</gif>", reply, re.DOTALL)
        gif_url = None
        if gif_match:
            gif_query = gif_match.group(1).strip()
            gif_url = await self.bot.db.search_gif(gif_query)
            reply = re.sub(r"<gif>.*?</gif>", "", reply, flags=re.DOTALL).strip()
        reply = self.bot.llm.strip_markers(reply)
        if reply:
            await message.reply(reply)
            hist.append({"role": "assistant", "content": reply})
        if gif_url:
            await message.channel.send(gif_url)
        print(f"DEBUG - Current History: {list(hist)}") 
        
        return

async def setup(bot):
    await bot.add_cog(ChatCog(bot))