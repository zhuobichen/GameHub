"""Reddit API 客户端"""
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.config import settings
from app.models import PlatformType

logger = logging.getLogger(__name__)


class RedditClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        self.client_id = client_id or settings.REDDIT_CLIENT_ID
        self.client_secret = client_secret or settings.REDDIT_CLIENT_SECRET
        self.user_agent = user_agent or settings.REDDIT_USER_AGENT
        self.access_token = None
        
    def calculate_score(self, score: int, num_comments: int, published_at: Optional[datetime] = None) -> float:
        """计算 Reddit 内容的综合评分"""
        final_score = 0.0
        
        # 基础指标
        final_score += min(score / 100, 10)  # Reddit Score (upvotes)
        final_score += min(num_comments / 50, 5)  # 评论数
        
        # 时间衰减
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            decay_factor = max(0.1, 1.0 - (days_since / 30))
            final_score *= decay_factor
            
        return final_score
        
    async def _get_access_token(self) -> Optional[str]:
        """获取 Reddit OAuth 访问令牌"""
        if not self.client_id or not self.client_secret:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                auth = (self.client_id, self.client_secret)
                data = {"grant_type": "client_credentials"}
                response = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=auth,
                    data=data,
                    headers={"User-Agent": self.user_agent},
                )
                response.raise_for_status()
                self.access_token = response.json().get("access_token")
                return self.access_token
        except Exception as e:
            logger.error(f"Reddit auth error: {e}")
            return None
            
    async def search_posts(self, query: str, max_results: int = 20, days: int = 30, subreddits: Optional[List[str]] = None) -> List[Dict]:
        """搜索 Reddit 帖子"""
        # 尝试使用官方 API，否则使用备用方法
        if self.client_id and self.client_secret:
            results = await self._search_with_api(query, max_results, days, subreddits)
            if results:
                return results
                
        return await self._search_with_json_endpoint(query, max_results, days, subreddits)
        
    async def _search_with_api(self, query: str, max_results: int = 20, days: int = 30, subreddits: Optional[List[str]] = None) -> List[Dict]:
        """使用官方 API 搜索"""
        try:
            token = await self._get_access_token()
            if not token:
                return []
                
            subreddit_part = "+".join(subreddits) if subreddits else "all"
            search_url = f"https://oauth.reddit.com/r/{subreddit_part}/search.json"
            
            params = {
                "q": query,
                "sort": "top",
                "t": "month" if days <= 30 else "year",
                "limit": max_results,
                "restrict_sr": "0",
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": self.user_agent,
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                return self._parse_posts(data.get("data", {}).get("children", []))
                
        except Exception as e:
            logger.error(f"Reddit API search error: {e}")
            return []
            
    async def _search_with_json_endpoint(self, query: str, max_results: int = 20, days: int = 30, subreddits: Optional[List[str]] = None) -> List[Dict]:
        """使用公开 JSON 端点（无 API Key）"""
        try:
            subreddit_part = "+".join(subreddits) if subreddits else "all"
            search_url = f"https://old.reddit.com/r/{subreddit_part}/search.json"
            
            params = {
                "q": query,
                "sort": "top",
                "t": "month",
                "limit": max_results,
                "restrict_sr": "off",
            }
            
            headers = {"User-Agent": self.user_agent}
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                return self._parse_posts(data.get("data", {}).get("children", []))
                
        except Exception as e:
            logger.error(f"Reddit JSON endpoint error: {e}")
            return await self._search_fallback(query, max_results)
            
    def _parse_posts(self, posts: List[Dict]) -> List[Dict]:
        """解析 Reddit 帖子数据"""
        results = []
        
        for post_wrapper in posts:
            post = post_wrapper.get("data", {})
            if not post:
                continue
                
            published_at = None
            if post.get("created_utc"):
                published_at = datetime.fromtimestamp(post["created_utc"])
                
            score_val = post.get("score", 0)
            num_comments = post.get("num_comments", 0)
            final_score = self.calculate_score(score_val, num_comments, published_at)
            
            results.append({
                "platform": PlatformType.REDDIT,
                "content_id": post.get("id", ""),
                "title": post.get("title", ""),
                "content": post.get("selftext", ""),
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "author": post.get("author", ""),
                "author_url": f"https://reddit.com/user/{post.get('author', '')}" if post.get("author") else "",
                "author_avatar": "",
                "views": 0,  # Reddit 不直接提供视图数
                "likes": score_val,
                "comments": num_comments,
                "shares": 0,
                "score": final_score,
                "thumbnail_url": post.get("thumbnail", "") if post.get("thumbnail") and "http" in post["thumbnail"] else "",
                "duration": None,
                "published_at": published_at,
                "metadata": {
                    "subreddit": post.get("subreddit", ""),
                    "ups": post.get("ups", 0),
                    "downs": post.get("downs", 0),
                    "upvote_ratio": post.get("upvote_ratio", 0),
                    "is_video": post.get("is_video", False),
                    "flair": post.get("link_flair_text", ""),
                },
            })
            
        return results
        
    async def _search_fallback(self, query: str, max_results: int = 20) -> List[Dict]:
        """备用搜索方法"""
        try:
            # 备用：直接搜索 r/gaming 等子版块
            search_url = "https://old.reddit.com/r/gaming/search.json"
            params = {
                "q": query,
                "sort": "top",
                "t": "month",
                "limit": max_results,
                "restrict_sr": "on",
            }
            
            headers = {"User-Agent": self.user_agent}
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_posts(data.get("data", {}).get("children", []))
                    
        except Exception as e:
            logger.error(f"Reddit fallback search error: {e}")
            
        return []
