"""小黑盒 (Xiaoheihe) 客户端 - 国内热门游戏社区"""
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.models import PlatformType

logger = logging.getLogger(__name__)


class XiaoheiheClient:
    BASE_URL = "https://api.xiaoheihe.cn"

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 xiaoheihe/5.0.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.xiaoheihe.cn/",
        }

    def calculate_score(self, likes: int, comments: int, views: int = 0, published_at: Optional[datetime] = None) -> float:
        score = 0.0
        score += min(likes / 50, 12)
        score += min(comments / 30, 8)
        if views:
            score += min(views / 5000, 5)
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            score *= max(0.15, 1.0 - (days_since / 21))
        return score

    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索小黑盒游戏相关帖子 - 从首页获取后客户端过滤"""
        try:
            # 小黑盒首页推荐流 + 游戏社区流
            endpoints = [
                f"{self.BASE_URL}/bbs/web/home",
                f"{self.BASE_URL}/v3/bbs/app/api/tag/list",
            ]

            all_posts = []
            async with httpx.AsyncClient(timeout=30) as client:
                for url in endpoints:
                    try:
                        r = await client.get(url, headers=self.headers, timeout=10)
                        if r.status_code == 200:
                            data = r.json()
                            posts = self._extract_posts(data, keyword, max_results, days)
                            all_posts.extend(posts)
                    except Exception as e:
                        logger.debug(f"Xiaoheihe {url}: {e}")
                        continue

            return all_posts[:max_results]
        except Exception as e:
            logger.error(f"Xiaoheihe search error: {e}")
            return []

    def _extract_posts(self, data: Dict, keyword: str, max_results: int, days: int) -> List[Dict]:
        results = []
        try:
            keyword_lower = keyword.lower()

            def walk(obj, depth=0):
                if depth > 8 or len(results) >= max_results:
                    return
                if isinstance(obj, list):
                    for item in obj:
                        if isinstance(item, dict):
                            walk(item, depth + 1)
                elif isinstance(obj, dict):
                    # Check if this looks like a post
                    title = obj.get("title") or obj.get("topic") or obj.get("subject") or ""
                    content = obj.get("content") or obj.get("summary") or obj.get("description") or ""
                    title_lower = (title + " " + content).lower()

                    if title and keyword_lower in title_lower:
                        post_id = str(obj.get("post_id") or obj.get("id") or obj.get("topic_id") or hash(title))
                        pub_time = obj.get("create_time") or obj.get("created_at") or obj.get("time")
                        published_at = None
                        if pub_time:
                            try:
                                if isinstance(pub_time, (int, float)):
                                    published_at = datetime.fromtimestamp(pub_time)
                                else:
                                    published_at = datetime.fromisoformat(str(pub_time))
                            except Exception:
                                pass

                        likes = obj.get("like_count") or obj.get("likes") or obj.get("like_num") or 0
                        comments = obj.get("comment_count") or obj.get("comments") or obj.get("reply_count") or 0
                        views = obj.get("view_count") or obj.get("views") or 0

                        author_info = obj.get("user") or obj.get("author") or {}
                        author = author_info.get("nickname") or author_info.get("name") or ""
                        avatar = author_info.get("avatar") or author_info.get("avatar_url") or ""

                        thumbnail = obj.get("cover") or obj.get("image") or ""
                        if not thumbnail:
                            imgs = obj.get("images") or []
                            if imgs:
                                thumbnail = imgs[0] if isinstance(imgs[0], str) else imgs[0].get("url", "")

                        score = self.calculate_score(likes, comments, views, published_at)
                        results.append({
                            "platform": PlatformType.XIAOHEIHE,
                            "content_id": post_id,
                            "title": title,
                            "content": content,
                            "url": f"https://www.xiaoheihe.cn/app/bbs/post/{post_id}",
                            "author": author,
                            "author_url": "",
                            "author_avatar": avatar,
                            "views": views,
                            "likes": likes,
                            "comments": comments,
                            "shares": 0,
                            "score": score,
                            "thumbnail_url": thumbnail,
                            "duration": None,
                            "published_at": published_at,
                            "metadata": {"source": "xiaoheihe"},
                        })

                    # Continue walking
                    for k, v in obj.items():
                        walk(v, depth + 1)

            walk(data)
        except Exception as e:
            logger.error(f"Xiaoheihe extract error: {e}")
        return results
