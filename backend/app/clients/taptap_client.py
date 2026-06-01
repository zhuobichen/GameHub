"""TapTap 客户端 - 国内手游平台"""
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.models import PlatformType

logger = logging.getLogger(__name__)


class TapTapClient:
    BASE_URL = "https://www.taptap.cn"
    API_BASE = "https://api.taptap.cn"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
            "Accept": "application/json",
        }
    
    def calculate_score(self, likes: int, replies: int, views: int = 0, published_at: Optional[datetime] = None) -> float:
        """计算 TapTap 内容评分 - 手游社区权重"""
        score = 0.0
        
        # TapTap 点赞和回复权重
        score += min(likes / 100, 12)
        score += min(replies / 50, 10)
        if views:
            score += min(views / 10000, 5)
        
        # 时间衰减
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            decay_factor = max(0.15, 1.0 - (days_since / 21))
            score *= decay_factor
            
        return score
    
    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索 TapTap 游戏相关内容"""
        try:
            # 使用 TapTap 搜索 API
            search_url = f"{self.API_BASE}/search"
            params = {
                "q": keyword,
                "type": "topic",  # 话题/帖子
                "limit": max_results,
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url, params=params, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_posts(data, keyword, days)
                    
        except Exception as e:
            logger.warning(f"TapTap API search failed: {e}")
            return await self._fallback_search(keyword, max_results, days)
        
        return []
    
    async def _fallback_search(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """备用搜索 - 直接访问热门游戏社区"""
        try:
            # 先搜索游戏再获取相关帖子
            game_search_url = f"{self.BASE_URL}/search"
            params = {"q": keyword}
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(game_search_url, params=params, headers=self.headers)
                if response.status_code == 200:
                    return self._extract_posts_from_page(response.text, keyword, days)
                    
        except Exception as e:
            logger.error(f"TapTap fallback search error: {e}")
            return []
    
    def _parse_posts(self, data: Dict, keyword: str, days: int) -> List[Dict]:
        """解析 TapTap 帖子数据"""
        results = []
        
        try:
            posts = []
            if "data" in data and isinstance(data["data"]):
                if isinstance(data["data"], list):
                    posts = data["data"]
                elif isinstance(data["data"], dict) and "list" in data["data"]:
                    posts = data["data"]["list"]
            
            for post in posts:
                try:
                    post_id = str(post.get("id", ""))
                    if not post_id:
                        continue
                        
                    title = post.get("title", "")
                    content = post.get("summary", "") or post.get("content", "")
                    
                    # 检查是否包含关键词
                    if keyword.lower() not in (title + content).lower():
                        continue
                    
                    published_at = None
                    if post.get("created_at"):
                        try:
                            if isinstance(post["created_at"], str):
                                published_at = datetime.fromisoformat(post["created_at"])
                            elif isinstance(post["created_at"], int):
                                published_at = datetime.fromtimestamp(post["created_at"])
                        except:
                            pass
                    
                    # 过滤时间范围
                    if published_at and days:
                        days_since = (datetime.utcnow() - published_at).days
                        if days_since > days:
                            continue
                    
                    # 互动数据
                    likes = post.get("likes", 0)
                    replies = post.get("replies", 0)
                    views = post.get("views", 0)
                    
                    # 作者信息
                    author_info = post.get("author", {}) or post.get("user", {})
                    author = author_info.get("name", "") or author_info.get("nickname", "")
                    author_avatar = author_info.get("avatar", "")
                    
                    # 封面图
                    thumbnail = ""
                    if post.get("images") and len(post["images"]) > 0:
                        thumbnail = post["images"][0]
                    elif post.get("image"):
                        thumbnail = post["image"]
                    
                    score = self.calculate_score(likes, replies, views, published_at)
                    
                    results.append({
                        "platform": PlatformType.TAPTAP,
                        "content_id": post_id,
                        "title": title,
                        "content": content,
                        "url": f"{self.BASE_URL}/post/{post_id}",
                        "author": author,
                        "author_url": "",
                        "author_avatar": author_avatar,
                        "views": views,
                        "likes": likes,
                        "comments": replies,
                        "shares": 0,
                        "score": score,
                        "thumbnail_url": thumbnail,
                        "duration": None,
                        "published_at": published_at,
                        "metadata": {
                            "source": "taptap",
                            "type": post.get("type", "post"),
                        },
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to parse TapTap post: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing TapTap data: {e}")
            
        return results
    
    def _extract_posts_from_page(self, html: str, keyword: str, days: int) -> List[Dict]:
        """从 HTML 页面提取帖子（备用方案）"""
        results = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # 查找帖子卡片
            post_cards = soup.find_all("div", class_=lambda x: x and ("post" in x.lower()))
            
            for card in post_cards[:20]:
                try:
                    title_elem = card.find("h3") or card.find("h2") or card.find(class_=lambda x: x and "title" in x.lower())
                    if not title_elem:
                        continue
                        
                    title = title_elem.get_text(strip=True)
                    if keyword.lower() not in title.lower():
                        continue
                    
                    results.append({
                        "platform": PlatformType.TAPTAP,
                        "content_id": str(hash(title)),
                        "title": title,
                        "content": "",
                        "url": self.BASE_URL,
                        "author": "",
                        "author_url": "",
                        "author_avatar": "",
                        "views": 0,
                        "likes": 0,
                        "comments": 0,
                        "shares": 0,
                        "score": 2.0,
                        "thumbnail_url": "",
                        "duration": None,
                        "published_at": None,
                        "metadata": {"source": "taptap-fallback"},
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to extract TapTap post from HTML: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing TapTap HTML: {e}")
            
        return results
