"""RAWG API 客户端"""
import httpx
from app.config import settings

BASE_URL = "https://api.rawg.io/api"


class RAWGClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or settings.RAWG_API_KEY

    async def _get(self, path: str, params: dict = None) -> dict:
        params = params or {}
        params["key"] = self.api_key
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{BASE_URL}{path}", params=params)
            resp.raise_for_status()
            return resp.json()

    async def search_games(self, query: str, page: int = 1) -> dict:
        return await self._get("/games", {
            "search": query,
            "page": page,
            "page_size": 20,
        })

    async def get_game(self, game_id: int) -> dict:
        return await self._get(f"/games/{game_id}")

    async def get_upcoming_games(self, page: int = 1) -> dict:
        from datetime import datetime, timedelta
        today = datetime.utcnow().strftime("%Y-%m-%d")
        future = (datetime.utcnow() + timedelta(days=365)).strftime("%Y-%m-%d")
        return await self._get("/games", {
            "dates": f"{today},{future}",
            "ordering": "-added",
            "page": page,
            "page_size": 40,
        })
