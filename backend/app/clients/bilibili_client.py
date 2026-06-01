"""Bilibili (B站) 客户端 - 国内最大视频社区"""
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.models import PlatformType

logger = logging.getLogger(__name__)


class BilibiliClient:
    BASE_URL = "https://www.bilibili.com"
    API_BASE = "https://api.bilibili.com"

    def __init__(self):
        self._cookies = None

    async def _get_cookies(self, client: httpx.AsyncClient):
        if self._cookies is None:
            r = await client.get(self.BASE_URL)
            self._cookies = r.cookies

    def calculate_score(self, views: int, likes: int, coins: int = 0, replies: int = 0, published_at: Optional[datetime] = None) -> float:
        score = 0.0
        score += min(views / 10000, 15)
        score += min(likes / 500, 12)
        score += min(coins / 200, 10)
        score += min(replies / 100, 8)
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            score *= max(0.15, 1.0 - (days_since / 21))
        return score

    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Referer": "https://www.bilibili.com/",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                await self._get_cookies(client)
                r = await client.get(
                    f"{self.API_BASE}/x/web-interface/search/type",
                    params={"keyword": keyword, "search_type": "video", "page": 1, "page_size": min(max_results, 50), "order": "click"},
                    headers=headers,
                    cookies=self._cookies,
                )
                if r.status_code != 200:
                    logger.warning(f"Bilibili API returned {r.status_code}")
                    return []
                data = r.json()
                return self._parse_videos(data, keyword, days)
        except Exception as e:
            logger.error(f"Bilibili search error: {e}")
            return []

    def _parse_videos(self, data: Dict, keyword: str, days: int) -> List[Dict]:
        results = []
        try:
            videos = []
            if data.get("code") == 0 and "data" in data:
                videos = data["data"].get("result", [])

            for video in videos:
                try:
                    bvid = video.get("bvid", "")
                    if not bvid:
                        continue

                    title = video.get("title", "").replace('<em class="keyword">', '').replace('</em>', '')
                    description = video.get("description", "")

                    pubdate = video.get("pubdate", 0)
                    if pubdate:
                        published_at = datetime.fromtimestamp(pubdate)
                        if days and (datetime.utcnow() - published_at).days > days:
                            continue
                    else:
                        published_at = None

                    views = video.get("play", 0)
                    likes = video.get("like", 0)
                    coins = video.get("coin", 0)
                    replies = video.get("video_review", 0)
                    author = video.get("author", "")
                    mid = video.get("mid", 0)
                    pic = video.get("pic", "")
                    duration = video.get("duration", "")

                    score = self.calculate_score(views, likes, coins, replies, published_at)

                    results.append({
                        "platform": PlatformType.BILIBILI,
                        "content_id": bvid,
                        "title": title,
                        "content": description,
                        "url": f"{self.BASE_URL}/video/{bvid}",
                        "author": author,
                        "author_url": f"{self.BASE_URL}/space/{mid}" if mid else "",
                        "author_avatar": "",
                        "views": views,
                        "likes": likes,
                        "comments": replies,
                        "shares": 0,
                        "score": score,
                        "thumbnail_url": pic,
                        "duration": duration,
                        "published_at": published_at,
                        "metadata": {"source": "bilibili", "coins": coins, "type": "video"},
                    })
                except Exception as e:
                    logger.debug(f"Parse Bilibili video error: {e}")
                    continue
        except Exception as e:
            logger.error(f"Bilibili parse error: {e}")
        return results
