"""YouTube API 客户端"""
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Optional
from app.config import settings
from app.models import PlatformType

logger = logging.getLogger(__name__)


class YouTubeClient:
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        
    def calculate_score(self, views: int, likes: int, comments: int, published_at: Optional[datetime] = None) -> float:
        """计算内容的综合评分 - 参考 last30days-skill 的评分机制"""
        score = 0.0
        
        # 基础指标评分
        score += min(views / 10000, 10)  # 观看量
        score += min(likes / 1000, 10)   # 点赞量
        score += min(comments / 100, 5)  # 评论量
        
        # 时间衰减因子 - 越新的内容分数越高
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            decay_factor = max(0.1, 1.0 - (days_since / 30))
            score *= decay_factor
            
        return score
        
    async def search_videos(self, query: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索游戏相关视频"""
        if not self.api_key:
            logger.warning("YOUTUBE_API_KEY not set, using fallback method")
            return await self._fallback_search(query, max_results)
            
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # 搜索视频
                search_params = {
                    "key": self.api_key,
                    "q": query,
                    "part": "snippet",
                    "type": "video",
                    "maxResults": max_results,
                    "order": "viewCount",
                    "videoDefinition": "high",
                }
                
                # 如果需要按时间过滤
                if days:
                    from datetime import timedelta
                    after_date = datetime.utcnow() - timedelta(days=days)
                    search_params["publishedAfter"] = after_date.isoformat("T") + "Z"
                
                search_response = await client.get(f"{self.BASE_URL}/search", params=search_params)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                # 获取视频详情（包含统计数据）
                video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])]
                if not video_ids:
                    return []
                
                videos_params = {
                    "key": self.api_key,
                    "id": ",".join(video_ids),
                    "part": "snippet,contentDetails,statistics",
                }
                
                videos_response = await client.get(f"{self.BASE_URL}/videos", params=videos_params)
                videos_response.raise_for_status()
                videos_data = videos_response.json()
                
                results = []
                for item in videos_data.get("items", []):
                    snippet = item.get("snippet", {})
                    stats = item.get("statistics", {})
                    content_details = item.get("contentDetails", {})
                    
                    published_at = None
                    if snippet.get("publishedAt"):
                        try:
                            published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
                        except:
                            pass
                            
                    # 解析时长 (ISO 8601 格式)
                    duration = self._parse_duration(content_details.get("duration", ""))
                    
                    views = int(stats.get("viewCount", 0))
                    likes = int(stats.get("likeCount", 0))
                    comments = int(stats.get("commentCount", 0))
                    
                    score = self.calculate_score(views, likes, comments, published_at)
                    
                    results.append({
                        "platform": PlatformType.YOUTUBE,
                        "content_id": item["id"],
                        "title": snippet.get("title", ""),
                        "content": snippet.get("description", ""),
                        "url": f"https://www.youtube.com/watch?v={item['id']}",
                        "author": snippet.get("channelTitle", ""),
                        "author_url": f"https://www.youtube.com/channel/{snippet.get('channelId', '')}",
                        "author_avatar": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
                        "views": views,
                        "likes": likes,
                        "comments": comments,
                        "shares": 0,  # YouTube API 不直接提供分享数
                        "score": score,
                        "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                        "duration": duration,
                        "published_at": published_at,
                        "metadata": {
                            "channel_id": snippet.get("channelId"),
                            "tags": snippet.get("tags", []),
                            "category_id": snippet.get("categoryId"),
                        },
                    })
                    
                return results
                
        except Exception as e:
            logger.error(f"YouTube API error: {e}")
            return await self._fallback_search(query, max_results)
            
    async def _fallback_search(self, query: str, max_results: int = 20) -> List[Dict]:
        """无 API Key 时的备用搜索方法（使用 RSS Feed）"""
        try:
            import feedparser
            from urllib.parse import quote
            
            search_url = f"https://www.youtube.com/feeds/videos.xml?search_query={quote(query)}"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url)
                feed = feedparser.parse(response.text)
                
                results = []
                for entry in feed.entries[:max_results]:
                    video_id = entry.get("yt_videoid", "")
                    published_at = None
                    if entry.get("published"):
                        from dateutil import parser
                        try:
                            published_at = parser.parse(entry.published)
                        except:
                            pass
                    
                    results.append({
                        "platform": PlatformType.YOUTUBE,
                        "content_id": video_id,
                        "title": entry.get("title", ""),
                        "content": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "author": entry.get("author", ""),
                        "author_url": entry.get("author_detail", {}).get("href", ""),
                        "author_avatar": "",
                        "views": 0,
                        "likes": 0,
                        "comments": 0,
                        "shares": 0,
                        "score": 1.0,
                        "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                        "duration": None,
                        "published_at": published_at,
                        "metadata": {"source": "rss_feed"},
                    })
                    
                return results
                
        except Exception as e:
            logger.error(f"YouTube fallback search error: {e}")
            return []
            
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """解析 ISO 8601 时长格式 (PT1H2M3S)"""
        if not duration_str:
            return None
            
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if not match:
            return None
            
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
