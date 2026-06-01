"""Steam API 客户端"""
import httpx
from app.config import settings

BASE_URL = "https://api.steampowered.com"
STORE_URL = "https://store.steampowered.com/api"


class SteamAPIClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.STEAM_API_KEY

    async def _get(self, url: str, params: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    async def get_app_list(self) -> list:
        """获取所有 Steam 应用列表"""
        data = await self._get(f"{BASE_URL}/ISteamApps/GetAppList/v2/")
        return data.get("applist", {}).get("apps", [])

    async def get_app_details(self, app_id: int, lang: str = "schinese") -> dict | None:
        """获取游戏详情（含中文信息、价格）"""
        params = {"appids": app_id, "l": lang, "cc": "CN"}
        data = await self._get(f"{STORE_URL}/appdetails", params)
        app_data = data.get(str(app_id), {})
        if app_data.get("success"):
            return app_data["data"]
        return None

    async def get_current_players(self, app_id: int) -> int:
        """获取当前在线人数"""
        data = await self._get(
            f"{BASE_URL}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/",
            {"appid": app_id},
        )
        return data.get("response", {}).get("player_count", 0)

    async def get_owned_games(self, steam_id: str) -> list:
        """获取用户游戏库"""
        data = await self._get(
            f"{BASE_URL}/IPlayerService/GetOwnedGames/v1/",
            {
                "key": self.api_key,
                "steamid": steam_id,
                "include_appinfo": 1,
                "include_played_free_games": 1,
                "format": "json",
            },
        )
        return data.get("response", {}).get("games", [])

    async def get_game_news(self, app_id: int, count: int = 5) -> list:
        """获取游戏新闻"""
        data = await self._get(
            f"{BASE_URL}/ISteamNews/GetNewsForApp/v2/",
            {"appid": app_id, "count": count, "maxlength": 300, "format": "json"},
        )
        return data.get("appnews", {}).get("newsitems", [])
