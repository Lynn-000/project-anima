import os
import re
from dotenv import load_dotenv
load_dotenv()
class Config:
    TOKEN = os.getenv("DISCORD_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "0"))
    GUILD_ID = int(os.getenv("GUILD_ID", "0"))
    ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID", "0"))
    CHAT_MODEL = "anima-bot"
    EDICT_MODEL = "anima-bot"
    CMD_PATTERN = re.compile(r"^(笞|杖|徒|流|死)\s+<@!?(\d+)>(?:\s+(\d+)(s|m|h|d))?$")
    UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    NOBILITY_PATTERN = re.compile(r"(封)\s+<@!?(\d+)>\s+(.+)$")
    ARCHIVE_PATTERN = re.compile(r"^(记)\s+<@!?(\d+)>\s*(.+)$")
    CYCLE_PATTERN = re.compile(r"(单曲|列表|无)$")
    NICKNAMES = ["CUSTOM"]
    COOLDOWN_SECONDS = 10
    AFFECTION_DEBUG = re.compile(r"^(查好感)\s+<@!?(\d+)>$")
    PLAY_PATTERN = re.compile(r"^播放\s+(.+)$")