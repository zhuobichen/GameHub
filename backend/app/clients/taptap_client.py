"""TapTap 客户端 - 国内手游平台"""
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.models import PlatformType

logger = logging.getLogger(__name__)


class TapTapClient:
    BASE_URL = "https://www.taptap.cn"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }

    def calculate_score(self, likes: int = 0, replies: int = 0, views: int = 0, published_at: Optional[datetime] = None) -> float:
        score = 0.0
        score += min(likes / 100, 12)
        score += min(replies / 50, 10)
        if views:
            score += min(views / 10000, 5)
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            score *= max(0.15, 1.0 - (days_since / 21))
        return score

    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索 TapTap 游戏相关内容 - 使用网页搜索"""
        try:
            search_url = f"{self.BASE_URL}/search/{keyword.replace(' ', '+')}"
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                r = await client.get(search_url, headers=self.headers)
                if r.status_code != 200:
                    logger.warning(f"TapTap search returned {r.status_code}")
                    return []
                return self._parse_search_page(r.text, keyword, max_results, days)
        except Exception as e:
            logger.error(f"TapTap search error: {e}")
            return []

    def _parse_search_page(self, html: str, keyword: str, max_results: int, days: int) -> List[Dict]:
        results = []
        try:
            from bs4 import BeautifulSoup
            import re
            import json

            soup = BeautifulSoup(html, "html.parser")

            # Try to extract JSON-LD / __NEXT_DATA__ first
            for script in soup.find_all("script"):
                text = script.string or ""
                if "__NEXT_DATA__" in text or '"props"' in text:
                    try:
                        data = json.loads(text)
                        # Walk nested data to find game list
                        def walk(obj, depth=0):
                            if depth > 10 or isinstance(obj, (str, int, float, bool)):
                                return
                            if isinstance(obj, list):
                                for item in obj[:max_results]:
                                    if isinstance(item, dict):
                                        name = item.get("name") or item.get("title") or ""
                                        if name and keyword.lower() in name.lower():
                                            results.append(self._make_result(item, keyword))
                                return
                            if isinstance(obj, dict):
                                for k in ("list", "apps", "games", "results", "items"):
                                    if k in obj and isinstance(obj[k], list):
                                        walk(obj[k], depth + 1)
                                        if results:
                                            return
                                walk(obj, depth + 1)
                        walk(data)
                    except (json.JSONDecodeError, AttributeError):
                        pass

            # Fallback: parse game cards from HTML
            if not results:
                cards = soup.find_all("a", href=re.compile(r"/app/\d+"))
                seen = set()
                for card in cards[:max_results]:
                    name = card.get_text(strip=True)
                    href = card.get("href", "")
                    if name and name not in seen and len(name) > 1:
                        seen.add(name)
                        results.append({
                            "platform": PlatformType.TAPTAP,
                            "content_id": str(hash(href)),
                            "title": name,
                            "content": "",
                            "url": f"{self.BASE_URL}{href}" if href.startswith("/") else href,
                            "author": "",
                            "author_url": "",
                            "author_avatar": "",
                            "views": 0,
                            "likes": 0,
                            "comments": 0,
                            "shares": 0,
                            "score": 3.0,
                            "thumbnail_url": "",
                            "duration": None,
                            "published_at": None,
                            "metadata": {"source": "taptap"},
                        })
        except ImportError:
            logger.warning("BeautifulSoup not available for TapTap")
        except Exception as e:
            logger.error(f"TapTap parse error: {e}")
        return results[:max_results]

    def _make_result(self, item: dict, keyword: str) -> Dict:
        name = item.get("name") or item.get("title") or keyword
        app_id = item.get("id", "")
        return {
            "platform": PlatformType.TAPTAP,
            "content_id": str(app_id),
            "title": name,
            "content": item.get("description") or item.get("summary", ""),
            "url": f"{self.BASE_URL}/app/{app_id}" if app_id else self.BASE_URL,
            "author": item.get("developer", ""),
            "author_url": "",
            "author_avatar": item.get("icon", ""),
            "views": 0,
            "likes": item.get("likes", 0),
            "comments": item.get("comments", 0),
            "shares": 0,
            "score": self.calculate_score(item.get("likes", 0), item.get("comments", 0)),
            "thumbnail_url": item.get("icon", "") or item.get("cover", ""),
            "duration": None,
            "published_at": None,
            "metadata": {"source": "taptap", "rating": item.get("rating", 0)},
        }
