import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from core.database import Database
from core.llm import LLMS
from core.config import Config
load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
class SakikoBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.config = Config()
        self.db = Database(owner_id = self.config.OWNER_ID)
        self.llm = LLMS(self.db)
    async def setup_hook(self):
        await self.load_extension("cogs.chat")
        await self.load_extension("cogs.music")
        await self.load_extension("cogs.punishment")
        await self.load_extension("cogs.management")
        await self.load_extension("cogs.affection")
        print("Finished loading all modules.")
    async def on_ready(self):
        print(f"logged in as {self.user}")
bot = SakikoBot()
bot.run(os.getenv("DISCORD_TOKEN"))