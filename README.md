**Disclaimer**: This is an unofficial, non-commercial fan project created for entertainment purposes. It is not affiliated with, endorsed, or sponsored by Bushiroad or the BanG Dream! Project. All character names and related elements are the intellectual property of their respective owners. The character "Togawa Sakiko" is used for **DEMONSTRATION PURPOSE** only. 

# Project-Anima 心弦
Project-Anima is a low to zero cost, highly customizable discord chat bot, with multiple functions, long-term memory, dynamic affection rating and dynamic response based on different users, built based on Large Language Model (gemma 4 from ollama) and Discord.py.
心弦是一个低/无成本高度可定制的discord聊天机器人，并具有多项功能，长期记忆，动态好感度以及基于不同成员的动态回应。该项目基于大语言模型(gemma 4 from ollama)和Discord.py构建。

"Note: The provided Modelfile is a demo persona (Togawa Sakiko). You can freely edit the SYSTEM prompt in Modelfile to create your own Anima (e.g., a different anime character or a generic assistant)."

Note that the bot replies to every message even without being mentioned with an internal cooldown of 10 seconds. Mentioning the bot/Including the bot's nickname (Customized in config.py) will refresh the cooldown.
**You can edit the OWNER_CONTEXT in llm.py.**

## Features 核心特性
- 🧠 **Hybrid Memory Architecture 混合记忆架构**
  - **Short-term**: Sliding window (`deque`) for contextual continuity without token overflow.
  - **Long-term**: SQLite persistence for user profiles, titles, and historical records.
  - 短期使用滑动窗口维持上下文连贯，长期基于 SQLite 持久化存储用户画像、头衔与历史记录。

- ❤️ **Dynamic Affection System 动态好感度系统**
  - Extracts hidden tags (e.g., `<affectionate> x </affectionate>`) to dynamically adjust the AI's attitude and tone in real-time. Features anti-farming and overflow protection.
  - 通过解析模型输出的隐藏标签，实时调整 AI 对特定用户的态度与语气。自带防恶意刷分与数值溢出保护机制。

- 👁️ **Multimodal Vision 多模态视觉感知**
  - Integrated Vision-Language Model (VLM) support. Can analyze images, extract text (OCR), and provide in-character critiques.
  - 集成视觉模型，支持识图、文字提取（OCR），并根据图片内容进行符合人设的无情锐评。

- ⚔️ **Roleplay & Governance 角色扮演与赛博朝政**
  - Features built-in "Five Penalties" (Mute/Kick/Ban) and "Nobility" systems. Automatically generates classical Chinese edicts based on events. You can use the "Nobility" systems to give custom roles. You can manually require the bot to remember something about a person.
  - 内置“五刑”（禁言/踢出/封禁）与“封爵修史”系统，能根据处罚或封赏事件自动生成文言文诏书。你可以利用封爵系统给予成员自定义身份，并手动要求心弦记录某人做过的某件事情。

- 🎵 **Async Music Player 异步点歌台**
  - FIFO queue system for local `.mp3` files. Supports loop, skip, and secure path traversal prevention.
  - 基于 FIFO 队列的本地音频播放器，支持单曲/列表循环、无缝切歌，并包含防路径穿越的安全机制。

- 🛡️ **Prompt Injection Defense 越狱防御**
  - Deeply customized System Prompt to resist logical loops and injection attacks, keeping the character strictly in-persona.
  - 深度定制的系统提示词，有效抵御逻辑死循环与提示词注入攻击，保持角色绝对不 OOC（出戏）。

## 🛠️ Tech Stack 技术栈

- **Language**: Python 3.10+
- **Core**: `discord.py` (Asyncio)
- **LLM Engine**: [Ollama](https://ollama.com/)
- **Database**: `sqlite3`
- **Audio**: `FFmpeg`

## 🚀 Quick Start 快速开始

### 1. Prerequisites 环境准备
- Install [Python](https://www.python.org/) (3.10+)
- Install [FFmpeg](https://ffmpeg.org/) and add it to your system `PATH`.
- Install [Ollama](https://ollama.com/) and ensure the service is running.
- Sign in to Ollama with `ollama signin` in command prompt (as the bot runs based on the free cloud model "gemma4").

### 2. Build the Model 构建模型
Build the custom persona using the provided `Modelfile` (The Modelfile is highly customizable. You can train it however you want, but better keep the special formats and safety protocol untouched.) :
使用提供的 `Modelfile` 构建心弦的人格（Modelfile是高度可定制的，你可以随意训练心弦以获得期望的效果，但最好不要乱动Modelfile里面的特别格式以及安全协议。）：

```bash
ollama create anima-bot -f ./Modelfile
```
### 3. Run the Model 运行模型
Double click ollama_run.bat to run the model.
双击 ollama_run.bat以运行模型。

### 4. Configuration 配置文件
Copy .env.example to .env and fill in your Discord Bot Token, Server ID, and Channel ID.
复制 .env.example 文件并重命名为 .env，填入你的 Discord Bot Token、服务器 ID 和频道 ID。

```bash
cp .env.example .env
```

### 5. Activate the bot 运行机器人
Windows: Run start.bat.
Mac/Linux: Run python main.py.
执行 start.bat 运行机器人


## 🎮 Commands 指令大全

*(Note: The bot only responds in the designated `TARGET_CHANNEL_ID`. Prefixes like `@Bot` or the bot's nickname are required for most commands.)*

### 💬 1. Basic Chat 基础聊天
| Command 指令 | Description 描述 |
| :--- | :--- |
| `@Bot <message>` | Chat with the bot directly. 直接与机器人对话。 |
| `<nickname> <message>` | Trigger the bot by calling its nickname. 通过呼唤昵称触发。 |
| *(Send an Image)* | The bot will analyze the image and reply. 发送图片，机器人会读取图片内容并回应。 |

### 🎵 2. Music Player 音乐点歌台
*(The user must be in a voice channel first. 用户必须先加入语音频道。)*
| Command 指令 | Description 描述 |
| :--- | :--- |
| `@Bot 播放 <song_name>` | Add a local song to the queue. 点歌（需确保 `music/` 文件夹有同名 `.mp3`）。 |
| `@Bot 切歌` or `skip` | Skip the current song. 切歌。 |
| `@Bot 单曲` / `列表` / `无` | Set loop mode: Single / List / None. 设置循环模式：单曲/列表/无。 |
| `@Bot 离开` or `退下` | Disconnect from the voice channel. 让机器人退出语音频道。 |

### ⚔️ 3. Five Penalties 五刑系统 (Admin Only)
*(Requires Administrator permissions or the configured `ADMIN_ROLE_ID`. 需管理员权限。)*
*Format 格式: `@Bot <penalty> <@user> [duration] [reason]`*
| Command 指令 | Description 描述 |
| :--- | :--- |
| `@Bot 笞 <@user> 10s` | Mute (Timeout) for 10 seconds. 禁言 10 秒 (默认单位: 秒)。 |
| `@Bot 杖 <@user> 5m` | Mute for 5 minutes. 禁言 5 分钟 (默认单位: 分钟)。 |
| `@Bot 徒 <@user> 1d` | Mute for 1 day. 禁言 1 天 (默认单位: 天)。 |
| `@Bot 流 <@user>` | Kick the user from the server. 踢出服务器。 |
| `@Bot 死 <@user>` | Ban the user from the server. 封禁用户。 |
*(After execution, the bot generates a classical Chinese edict. 执行后，机器人会自动生成对应的文言文处罚诏书。)*

### 👑 4. Governance 朝政系统 (Owner Only)
*(Only the `OWNER_ID` can execute these commands. 只有创作者/服主可以执行。)*
| Command 指令 | Description 描述 |
| :--- | :--- |
| `@Bot 封 <@user> <title>` | Grant a title to a user (e.g., `封 @xxx 汉王`). 封爵，给予用户头衔。 |
| `@Bot 记 <@user> <event>` | Record a historical event/black history for a user (e.g., `记 @xxx 打游戏红温`). 修史，记录某人的黑历史或事件。 |
| `@Bot 记 <@user> <event> <url>` | Record an event with a URL link as evidence. 带证据链接的修史。 |
*(After execution, the bot generates a classical Chinese edict. 执行后，机器人会自动生成对应的文言文处罚诏书。)*

### ❤️ 5. Debug & Status 状态查询
| Command 指令 | Description 描述 |
| :--- | :--- |
| `@Bot 查好感 <@user>` | Check the bot's affection rating towards a specific user. 查询心弦对某人的好感度分数。 |

**LICENSE**

This project is licensed under the GNU AGPL-3.0 License. Any derivative works or network services based on this project must be open-sourced.
本项目基于 GNU AGPL-3.0 License 协议开源。任何基于本项目的衍生作品或网络服务必须开源。

