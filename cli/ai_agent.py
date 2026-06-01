"""GameHub AI 推荐引擎 — DeepSeek V4 Pro"""
import json
from openai import OpenAI
from config import DEEPSEEK_API_KEY

_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

SYSTEM_PROMPT = "你是一个专业的游戏推荐顾问，擅长根据玩家的游戏库分析其偏好，给出精准的个性化推荐。回答用中文，保持热情但不啰嗦。"


def _build_profile(library: list, preferences: dict = None) -> str:
    if not library:
        return "暂无 Steam 游戏库数据"

    sorted_games = sorted(library, key=lambda g: g.get("playtime_forever", 0), reverse=True)

    profile = "## Steam 游戏库 (按游玩时间排序)\n"
    for g in sorted_games[:30]:
        name = g.get("name", "Unknown")
        hours = g.get("playtime_forever", 0) / 60
        recent = g.get("playtime_2weeks", 0) / 60
        profile += f"- {name}: {int(hours)}h"
        if recent > 0:
            profile += f" (近两周 {recent:.1f}h)"
        profile += "\n"

    if preferences:
        profile += "\n## 用户偏好设置\n"
        for k, v in preferences.items():
            if v:
                profile += f"- {k}: {', '.join(v)}\n"

    return profile


def ask(library: list, preferences: dict, question: str) -> str:
    if not DEEPSEEK_API_KEY:
        return "[错误] 未设置 DEEPSEEK_API_KEY"

    profile = _build_profile(library, preferences)

    prompt = f"""你是一个游戏推荐专家。以下是用户的游戏库和偏好：

{profile}

用户提问：{question}

请根据用户的游戏库、游玩时长和偏好，给出个性化的、有洞察的回答。可以：
- 推荐类似的游戏
- 分析用户的游戏偏好模式
- 建议库里哪些游戏值得补玩
- 针对用户口味筛选即将发售的游戏

请用中文回答，保持简洁有料。"""

    response = _client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content


def analyze_taste(library: list, preferences: dict) -> str:
    return ask(library, preferences, "详细分析我的游戏偏好和口味，包括：我喜欢的类型、我的游玩模式（通关型/刷刷刷型/社交型）、我的隐藏偏好，以及可能适合但我库里没有的游戏类型。")


def recommend_games(library: list, preferences: dict, count: int = 5) -> str:
    return ask(library, preferences, f"根据我的游戏库，推荐 {count} 款我可能喜欢但还没买的游戏。给出具体的推荐理由，每个推荐引用我库里玩过的类似游戏作为依据。")


def recommend_news(library: list, preferences: dict) -> str:
    return ask(library, preferences, "基于我的游戏偏好，我应该关注哪些游戏资讯？有哪些我玩过的游戏最近有大更新、DLC或续作消息？")
