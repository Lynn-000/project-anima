import discord
import re
import asyncio
from discord.ext import commands
from pathlib import Path

def create_ffmpeg_source(filepath: str):
    return discord.FFmpegPCMAudio(filepath, options="-vn")
class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.MUSIC_QUEUE = []
        self.current_song = None
        self.cycle_mode = "None"
        self.parse_lock = asyncio.Lock()

    def switch_cycle(self, mode):
        if mode in ["Single", "List", "None"]:
            self.cycle_mode = mode

    async def play_next(self, message, vc):
        if self.current_song is not None:
            if self.cycle_mode == "Single":
                self.MUSIC_QUEUE.insert(0, self.current_song)
            elif self.cycle_mode == "List":
                self.MUSIC_QUEUE.append(self.current_song)
            self.current_song = None
        if not self.MUSIC_QUEUE:
            await message.channel.send("播完了，退朝。")
            await vc.disconnect()
            return
        song_name = self.MUSIC_QUEUE.pop(0)
        self.current_song = song_name
        base_dir = Path(__file__).resolve().parent.parent
        filepath = base_dir / "music" / f"{song_name}.mp3"
        if not filepath.exists():
            await message.channel.send(f"本地曲库里没有《{song_name}》，换一首吧。")
            self.current_song = None
            await self.play_next(message, vc)
            return
        def after_playing(error):
            if error:
                print(f'播放出错: {error}')
            async def next_song():
                await asyncio.sleep(0.5)
                await self.play_next(message, vc)
            self.bot.loop.create_task(next_song())
        try:
            source = create_ffmpeg_source(str(filepath))
            vc.play(source, after=after_playing)
            await message.channel.send(f"正在播放：{song_name}")
        except Exception as e:
            print(f"播放异常: {e}")
            await message.channel.send("播放失败了，跳到下一首。")
            self.current_song = None
            await self.play_next(message, vc)
class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.player = MusicPlayer(bot)
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
        if content.lower() in ["skip", "切歌"]:
            vc = message.guild.voice_client
            if vc and vc.is_playing() and not self.player.parse_lock.locked():
                vc.stop()
                await message.reply("已切歌。")
            else:
                await message.reply("现在没在放歌。")
            return
        if content in ["离开", "退下"]:
            vc = message.guild.voice_client
            if vc and vc.is_connected():
                self.player.MUSIC_QUEUE.clear()
                self.player.current_song = None
                await vc.disconnect()
                await message.reply("哼，这点杂音也配让我一直听着？")
            else:
                await message.reply("我根本不在语音频道里。")
            return
        if content in ["单曲", "列表", "无"]:
            if content == "单曲":
                self.player.switch_cycle("Single")
            elif content == "列表":
                self.player.switch_cycle("List")
            elif content == "无":
                self.player.switch_cycle("None")
            await message.reply(f"循环模式已切换为：{content}。")
            return
        playmatch = self.bot.config.PLAY_PATTERN.match(content)
        if playmatch:
            raw_input = playmatch.group(1).strip()
            song_name = re.sub(r'[\\/:*?"<>|]', '', raw_input).strip()
            if not song_name:
                await message.reply("点歌失败：包含非法字符。")
                return
            if len(self.player.MUSIC_QUEUE) >= 100:
                await message.reply("当前队列太长了，晚点再点吧！")
                return
            if not message.author.voice or not message.author.voice.channel:
                await message.reply("你不在语音频道里，我进去给谁唱？")
                return
            vc_channel = message.author.voice.channel
            try:
                if message.guild.voice_client is None:
                    voice_client = await vc_channel.connect()
                else:
                    voice_client = message.guild.voice_client
                    if voice_client.channel != vc_channel:
                        await voice_client.move_to(vc_channel)
            except Exception as e:
                print(f"连接语音失败: {e}")
                await message.reply("我进不去，你打算让我怎么唱？")
                return
            await message.reply("正在加入队列...")
            self.player.MUSIC_QUEUE.append(song_name)
            if not voice_client.is_playing() and not voice_client.is_paused() and not self.player.parse_lock.locked():
                await self.player.play_next(message, voice_client)
            else:
                await message.reply(f"已加入队列，当前排在第 {len(self.player.MUSIC_QUEUE)} 位。")
            return

async def setup(bot):
    await bot.add_cog(MusicCog(bot))