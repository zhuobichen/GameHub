"""Hacker News API 客户端"""
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.models import PlatformType

logger = logging.getLogger(__name__)


class HackerNewsClient:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    def calculate_score(self, score: int, descendants: int, published_at: Optional[datetime] = None) -> float:
        """计算 Hacker News 内容评分"""
        final_score = 0.0
        
        # Hacker News 权重很高，因为是技术社区
        final_score += min(score / 50, 15)  # 点数权重更高
        final_score += min(descendants / 20, 8)  # 评论数
        
        # 时间衰减
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            decay_factor = max(0.2, 1.0 - (days_since / 60))
            final_score *= decay_factor
            
        return final_score
        
    async def search_stories(self, query: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索 Hacker News 故事"""
        try:
            # 使用 Algolia 搜索 API（官方推荐的搜索方式）
            search_url = "http://hn.algolia.com/api/v1/search"
            
            params = {
                "query": query,
                "tags": "story",
                "hitsPerPage": max_results,
            }
            
            if days:
                from datetime import timedelta
                after_date = datetime.utcnow() - timedelta(days=days)
                params["numericFilters"] = f"created_at_i>{int(after_date.timestamp())}"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return self._parse_stories(data.get("hits", []))
                
        except Exception as e:
            logger.error(f"Hacker News search error: {e}")
            return []
            
    def _parse_stories(self, stories: List[Dict]) -> List[Dict]:
        """解析 Hacker News 故事数据"""
        results = []
        
        for story in stories:
            published_at = None
            if story.get("created_at_i"):
                published_at = datetime.fromtimestamp(story["created_at_i"])
                
            score = story.get("points", 0)
            descendants = story.get("num_comments", 0)
            final_score = self.calculate_score(score, descendants, published_at)
            
            results.append({
                "platform": PlatformType.HACKER_NEWS,
                "content_id": str(story.get("objectID", "")),
                "title": story.get("title", ""),
                "content": story.get("story_text", "") or "",
                "url": story.get("url", "") or f"https://news.ycombinator.com/item?id={story.get('objectID', '')}",
                "author": story.get("author", ""),
                "author_url": f"https://news.ycombinator.com/user?id={story.get('author', '')}" if story.get("author") else "",
                "author_avatar": "",
                "views": 0,
                "likes": score,
                "comments": descendants,
                "shares": 0,
                "score": final_score,
                "thumbnail_url": "",
                "duration": None,
                "published_at": published_at,
                "metadata": {
                    "type": "story",
                    "story_id": story.get("objectID"),
                },
            })
            
        return results
