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
        }
    
    def calculate_score(self, likes: int, comments: int, views: int = 0, published_at: Optional[datetime] = None) -> float:
        """计算小黑盒内容的评分 - 国内社区权重调整"""
        score = 0.0
        
        # 小黑盒用户互动权重
        score += min(likes / 50, 12)  # 点赞权重较高
        score += min(comments / 30, 8)  # 评论权重也高
        if views:
            score += min(views / 5000, 5)  # 浏览量
        
        # 时间衰减
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            decay_factor = max(0.15, 1.0 - (days_since / 21))  # 21天衰减
            score *= decay_factor
            
        return score
    
    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索小黑盒游戏相关帖子"""
        try:
            # 使用小黑盒搜索 API
            search_url = f"{self.BASE_URL}/bbs/web/search/result"
            params = {
                "q": keyword,
                "type": "post",  # 搜索帖子
                "limit": max_results,
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url, params=params, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_posts(data, keyword, days)
                    
        except Exception as e:
            logger.warning(f"Xiaoheihe API search failed: {e}")
            # 尝试备用方法
            return await self._fallback_search(keyword, max_results, days)
        
        return []
    
    async def _fallback_search(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """备用搜索方法 - 直接抓取热门区"""
        try:
            hot_url = f"{self.BASE_URL}/bbs/web/official_recommend/get_list"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(hot_url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    posts = self._parse_posts(data, keyword, days)
                    # 过滤包含关键词的帖子
                    filtered = [
                        p for p in posts 
                        if keyword.lower() in (p.get("title", "") + " " + p.get("content", "")).lower()
                    ]
                    return filtered[:max_results]
                    
        except Exception as e:
            logger.error(f"Xiaoheihe fallback search error: {e}")
        
        return []
    
    def _parse_posts(self, data: Dict, keyword: str, days: int) -> List[Dict]:
        """解析小黑盒帖子数据"""
        results = []
        
        # 尝试多种数据结构
        posts = []
        if "result" in data and "posts" in data["result"]:
            posts = data["result"]["posts"]
        elif "data" in data and isinstance(data["data"], list):
            posts = data["data"]
        
        for post in posts:
            try:
                # 提取帖子信息
                post_id = str(post.get("post_id", post.get("id", "")))
                if not post_id:
                    continue
                    
                title = post.get("title", "")
                content = post.get("content", "") or post.get("summary", "")
                
                # 时间解析
                published_at = None
                if post.get("create_time"):
                    try:
                        if isinstance(post["create_time"], str):
                            published_at = datetime.fromisoformat(post["create_time"])
                        else:
                            published_at = datetime.fromtimestamp(post["create_time"])
                    except:
                        pass
                
                # 过滤时间范围
                if published_at and days:
                    days_since = (datetime.utcnow() - published_at).days
                    if days_since > days:
                        continue
                
                # 互动数据
                likes = post.get("like_count", post.get("likes", 0))
                comments = post.get("comment_count", post.get("comments", 0))
                views = post.get("view_count", post.get("views", 0))
                
                # 作者信息
                author_info = post.get("user", {}) or post.get("author", {})
                author = author_info.get("nickname", author_info.get("name", ""))
                author_avatar = author_info.get("avatar", "")
                
                # 封面图
                thumbnail = ""
                if post.get("cover"):
                    thumbnail = post["cover"]
                elif post.get("images") and len(post["images"]) > 0:
                    thumbnail = post["images"][0]
                
                score = self.calculate_score(likes, comments, views, published_at)
                
                results.append({
                    "platform": PlatformType.XIAOHEIHE,
                    "content_id": post_id,
                    "title": title,
                    "content": content,
                    "url": f"https://api.xiaoheihe.cn/bbs/app/post/share?post_id={post_id}",
                    "author": author,
                    "author_url": "",
                    "author_avatar": author_avatar,
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "shares": 0,
                    "score": score,
                    "thumbnail_url": thumbnail,
                    "duration": None,
                    "published_at": published_at,
                    "metadata": {
                        "source": "xiaoheihe",
                        "game_tag": post.get("game_name", ""),
                    },
                })
                
            except Exception as e:
                logger.debug(f"Failed to parse Xiaoheihe post: {e}")
                continue
                
        return results
