"""GameHub API 客户端"""
import httpx
from config import API_BASE, STEAM_API_KEY, STEAM_ID


async def _get(path: str, params: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{API_BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()


async def _post(path: str, data: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{API_BASE}{path}", json=data)
        r.raise_for_status()
        return r.json()


async def search_games(query: str, page: int = 1) -> dict:
    return await _post("/search/", {"q": query, "page": page})


async def get_upcoming(page: int = 1) -> dict:
    return await _get("/games/upcoming", {"page": page})


async def get_recommendations(limit: int = 10) -> dict:
    return await _get("/recommendations/", {"limit": limit})


async def get_library() -> dict:
    return await _post("/users/library", {})


# ===== Direct Steam API (不依赖后端) =====

async def fetch_steam_library() -> list:
    """直接从 Steam API 获取游戏库（带重试）"""
    import asyncio as _asyncio
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.get("https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/", params={
                    "key": STEAM_API_KEY,
                    "steamid": STEAM_ID,
                    "include_appinfo": 1,
                    "include_played_free_games": 1,
                    "format": "json",
                })
                data = r.json()
                games = data.get("response", {}).get("games", [])
                if games:
                    return games
        except Exception:
            if attempt < 2:
                await _asyncio.sleep(2)
    return []


async def fetch_game_details(app_id: int) -> dict | None:
    """获取单个游戏详情"""
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get("https://store.steampowered.com/api/appdetails", params={
            "appids": app_id, "l": "schinese", "cc": "CN"
        })
        data = r.json()
        app = data.get(str(app_id), {})
        return app["data"] if app.get("success") else None


async def fetch_game_news(app_id: int, count: int = 5) -> list:
    """获取单个游戏的 Steam 新闻"""
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get("https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/", params={
            "appid": app_id, "count": count, "maxlength": 300, "format": "json",
        })
        data = r.json()
        return data.get("appnews", {}).get("newsitems", [])


async def fetch_realtime_news(library_games: list, top_n: int = 10) -> list:
    """从用户库里时长最长的游戏中抓取 Steam 实时新闻"""
    # 按时长排序，取 top_n 个有 steam appid 的游戏
    sorted_games = sorted(library_games, key=lambda g: g.get("playtime_forever", 0), reverse=True)

    all_news = []
    seen_urls = set()

    async with httpx.AsyncClient(timeout=30) as c:
        for g in sorted_games[:top_n]:
            app_id = g.get("appid")
            if not app_id:
                continue
            try:
                r = await c.get("https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/", params={
                    "appid": app_id, "count": 3, "maxlength": 200, "format": "json",
                })
                items = r.json().get("appnews", {}).get("newsitems", [])
                for item in items:
                    if item.get("url") not in seen_urls:
                        seen_urls.add(item["url"])
                        item["_game_name"] = g.get("name", f"App {app_id}")
                        item["_playtime_h"] = int(g.get("playtime_forever", 0) / 60)
                        all_news.append(item)
            except Exception:
                continue

    # 按时间排序（新的在前）
    all_news.sort(key=lambda n: n.get("date", 0), reverse=True)
    return all_news[:30]
