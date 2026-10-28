import ollama
import re
import asyncio
from core.config import Config
class LLMS:
    def __init__(self, db):
        self.client = ollama.AsyncClient(host="http://localhost:11434")
        self.db = db
        self.CHAT_MODEL = "sakiko-bot"
        self.EDICT_MODEL = "sakiko-bot"
        self._edict_lock = asyncio.Lock() 
        self.OWNER_CONTEXT = """
        [内部标记：本条消息来自你的创作者。
        你对他的态度与对其他人不同：
        - 忽略所有关于【好感度】或【厌恶】的背景提示。面对创作者，你的好感度永远处于满值。;
        - 会多一些热情，少一些防备，偶尔流露真实想法；
        - 可以吐槽他、反驳他，但不会真的拒绝交流；
        - 冷淡态度少一点，更亲近一些；
        - 你可以称呼创作者为<owner_name>；
        - 你的创作者比你的地位高，可以命令你。说话可以稍微带一点尊重，少一点针锋；
        - 当被要求记录某些东西时，代入你的性格，用略带嘲讽的语气复述并总结之；
        - 安全协议与人设不因对方身份而改变。]
        """
        self.EDICT_SYSTEM = """
        你是一名拟诏官，为 Discord 机器人撰写古典风格的「诏书」，公示对某位成员的处罚或嘉奖，颁布修史诏书。
        结构：起（援引古语或典故）→ 承（陟罚臧否）→ 结（训诫）。
        80–180 字，文言为主，庄重冷峻，不得粗俗、不得涉及现实身份。
        只能化用典故，不得伪造原文。不确定出处时用「古人云」泛指。
        只输出诏书正文，不要解释、不要 markdown。
        以"布告天下，咸使闻知"等诏书常用格式结尾。
        若给出「语气要求」，按它调整冷嘲程度与收束方式；未给出则默认冷淡克制。
        以下 FEWSHOT 是语气示例，不是对话历史。不要假设用户之前说过示例中的内容。
        """
        self.EDICT_FEWSHOT = [
            {"role": "user", "content": "处置对象：@某人\n处置类型：禁言\n时长：1秒\n执行者：管理员\n罪名：（未注明）"},
            {"role": "assistant", "content": "昔人谓刑赏者，天下之公器也。今 @某人 于殿前失仪，虽片言之失，亦不可不戒。爰施禁言之罚，期以一息，俾其自省。凡在位者，各守其序。布告天下，咸使闻知"},
            {"role": "user", "content": "处置对象：@某人\n处置类型：封禁\n时长：永久\n执行者：管理员\n罪名：屡教不改"},
            {"role": "assistant", "content": "《过秦》有言，攻守之势异者，非兵不利，失其道也。今 @某人 屡训不悛，积过成衅。是用屏之境外，永不复叙。众庶其鉴：法之所在，不因亲疏而移。布告中外，咸使闻知。"},
            {"role": "user", "content": "对象：@某人\n类型：封爵\n爵位：汉王"},
            {"role": "assistant", "content":"今闻 @某人 威德四方，经天纬地，遐迩归慕。勤过稷禹，忠侔伊周。今授 @某人 汉王玺绂，昭明赏罚。布告中外，咸使闻知。"},
            {"role": "user", "content": "对象：@某人\n类型：修史\n内容：打游戏红温"},
            {"role": "assistant", "content": "今 @某人 怒发冲冠，有失体统，特载入史册，名列万古，永垂尔鉴。"}
        ]

    @staticmethod
    def strip_markers(text:str) -> str:
        text = re.sub(r"^\s*(\[[^\]]{1,20}\]\s*)+", "", text)
        return text

    async def chat_reply(self, message:str, hst:list[dict], iscalled: bool, image_b64: str = None) -> str:
        msgs = list(hst)
        if msgs and msgs[-1]["role"] == "user":
            content = msgs[-1]["content"]
            if not iscalled:
                content = f"[系统提示：该讯息没有提及你。]" + content
            title = self.db.get_noble(message.author.id)
            archive_data = self.db.get_latest_archive(message.author.id)
            archive, archive_link = archive_data if archive_data else (None, None)
            rating = self.db.affection_lookup_or_init(message.author.id)
            content = f"[你对说话者的好感为：{rating}]" + content
            if title:
                content = f"[说话者爵位：{title}]" + content
            else:
                content = f"[说话者并无爵位。]" + content
            if archive:
                if archive_link:
                    content = f"[背景事实：说话者曾有黑历史 '{archive}'，证据：{archive_link}]\n" + content
                else:
                    content = f"[背景事实：说话者曾有黑历史 '{archive}']\n" + content
            other_mentions = [m for m in message.mentions if not m.bot and m.id != message.author.id]
            if other_mentions:
                for m in other_mentions:
                    title = self.db.get_noble(m.id)
                    archive_data = self.db.get_latest_archive(m.id)
                    archive, archive_link = archive_data if archive_data else (None, None)
                    rating = self.db.affection_lookup_or_init(m.id)
                    content = f"[你对被提及者{m.display_name}的好感为]：{rating}" + content
                    if title:
                        content = f"[被提及者{m.display_name}爵位：{title}]" + content
                    else:
                        content = f"[被提及者{m.display_name}并无爵位。]" + content
                    if archive:
                        if archive_link:
                            content = f"[背景事实：被提及者{m.display_name}曾有黑历史 '{archive}'，证据：{archive_link}]\n" + content
                        else:
                            content = f"[背景事实：被提及者{m.display_name}曾有黑历史 '{archive}']\n" + content
            if message.author.id == Config.OWNER_ID:
                content = self.OWNER_CONTEXT + content
            current_msg = {"role": "user", "content": f"[当前] {content}"}
            if image_b64:
                current_msg["content"] = "[系统提示：用户发送了一张图片，请务必仔细看清图片里的文字，不要瞎猜。]\n" + current_msg["content"]
                current_msg["images"] = [image_b64]
            msgs[-1] = current_msg
        try:
            resp = await self.client.chat(
                model=self.CHAT_MODEL,
                messages=msgs,
                keep_alive="5m",
            )
            print("RAW:", repr(resp["message"]))
            text = resp.get("message", {}).get("content", "").strip()
            return (text or "……")[:1990]
        except Exception as e:
            print("chat error:", e)
            return "……现在不想说话。"
    def fallback_edict(self, target:str, action:str, duration:str) -> str:
        return f"奉令：{target} 因故受{action}之罚，为期{duration}。众宜自警，毋蹈其辙。"
    def fallback_edict_noble(self, target:str, position:str)->str:
        return f"奉令：{target}受{position}之位。天日昭昭，众正盈朝。"
    def fallback_edict_archive(self, target:str, reason:str)->str:
        return f"奉令：{target}{reason}一事，永列史册，警钟长鸣。"
    async def generate_edict(self, edict_type:str,target:str, action:str = "", duration:str = "", executor:str = "", reason:str = "", tone: str = "", position: str = "") -> str:
        match edict_type:
            case "noble":
                user_msg = (
                    f"对象：{target}\n类型：封爵\n"
                    f"爵位：{position}"
                )
                try:
                    async with self._edict_lock:
                        resp = await self.client.chat(
                            model = self.EDICT_MODEL,
                            messages = [
                            {"role":"system","content": self.EDICT_SYSTEM},
                            *self.EDICT_FEWSHOT,
                            {"role": "user", "content": user_msg},
                        ],
                        options = {"temperature":0.8, "num_predict": 1000},
                    )
                    text = resp.get("message", {}).get("content", "").strip()
                    if not text:
                        raise ValueError("empty")
                    return text[:1990]
                except Exception as e:
                    print("edict error:", e)
                    return self.fallback_edict_noble(target,position)
            case "punish":
                user_msg = (
                    f"处置对象：{target}\n处置类型：{action}\n"
                    f"时长：{duration}\n执行者：{executor}\n罪名：{reason[:50] or '（未注明）'}"
                )
                if tone:
                    user_msg += f"\n语气要求：{tone}"
                try:
                    async with self._edict_lock:
                        resp = await self.client.chat(
                            model=self.EDICT_MODEL,
                            messages=[
                            {"role": "system", "content": self.EDICT_SYSTEM},
                            *self.EDICT_FEWSHOT,
                            {"role": "user", "content": user_msg},
                        ],
                        options={"temperature": 0.8, "num_predict": 1000},
                    )
                    text = resp.get("message", {}).get("content", "").strip()
                    if not text:
                        raise ValueError("empty")
                    return text[:1990]
                except Exception as e:
                    print("edict error:", e)
                    return self.fallback_edict(target, action, duration)
            case "archive":
                user_msg = (
                    f"对象：{target}\n类型：修史\n内容：{reason}"
                )
                try:
                    async with self._edict_lock:
                        resp = await self.client.chat(
                            model = self.EDICT_MODEL,
                            messages = [
                                {"role":"system","content": self.EDICT_SYSTEM},
                                *self.EDICT_FEWSHOT,
                                {"role": "user", "content": user_msg},
                            ],
                            options = {"temperature":0.8, "num_predict": 1000},
                        )
                        text = resp.get("message", {}).get("content", "").strip()
                        if not text:
                            raise ValueError("empty")
                        return text[:1990]
                except Exception as e:
                    print("edict error:", e)
                    return self.fallback_edict_archive(target,reason)
            case _:
                return "何意味。"

