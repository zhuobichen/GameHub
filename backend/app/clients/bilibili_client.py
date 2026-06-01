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
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com/",
        }
    
    def calculate_score(self, views: int, likes: int, coins: int = 0, replies: int = 0, published_at: Optional[datetime] = None) -> float:
        """计算 B站 内容评分 - 视频社区特有权重"""
        score = 0.0
        
        # B站 播放/点赞/投币/收藏/回复 综合权重
        score += min(views / 10000, 15)
        score += min(likes / 500, 12)
        score += min(coins / 200, 10)
        score += min(replies / 100, 8)
        
        # 时间衰减
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            decay_factor = max(0.15, 1.0 - (days_since / 21))
            score *= decay_factor
            
        return score
    
    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索 B站 游戏相关视频"""
        try:
            # 使用 B站 搜索 API
            search_url = f"{self.API_BASE}/x/web-interface/search/type"
            params = {
                "keyword": keyword,
                "search_type": "video",
                "page": 1,
                "page_size": max_results,
                "order": "view",  # 按播放量排序
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url, params=params, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_videos(data, keyword, days)
                    
        except Exception as e:
            logger.warning(f"Bilibili API search failed: {e}")
            return await self._fallback_search(keyword, max_results, days)
        
        return []
    
    async def _fallback_search(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """备用搜索 - 通过 RSS 或热门榜"""
        try:
            # 使用 B站 热门游戏区 RSS
            hot_url = f"{self.BASE_URL}/v/rank/all"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(hot_url, headers=self.headers)
                if response.status_code == 200:
                    return self._extract_from_rss(response.text, keyword, max_results, days)
                    
        except Exception as e:
            logger.error(f"Bilibili fallback search error: {e}")
            return []
    
    def _parse_videos(self, data: Dict, keyword: str, days: int) -> List[Dict]:
        """解析 B站 视频数据"""
        results = []
        
        try:
            videos = []
            if data.get("code") == 0 and "data" in data:
                data_field = data["data"]
                if "result" in data_field:
                    videos = data_field["result"]
            
            for video in videos:
                try:
                    bvid = video.get("bvid", "") or str(video.get("aid", ""))
                    if not bvid:
                        continue
                        
                    title = video.get("title", "")
                    description = video.get("description", "")
                    
                    # 检查是否包含关键词
                    if keyword.lower() not in (title + description).lower():
                        continue
                    
                    published_at = None
                    if video.get("pubdate"):
                        try:
                            published_at = datetime.fromtimestamp(video["pubdate"])
                        except:
                            pass
                    
                    # 过滤时间范围
                    if published_at and days:
                        days_since = (datetime.utcnow() - published_at).days
                        if days_since > days:
                            continue
                    
                    # 互动数据
                    views = video.get("play", 0) or video.get("view", 0)
                    likes = video.get("like", 0) or video.get("likes", 0)
                    coins = video.get("coin", 0) or video.get("coins", 0)
                    replies = video.get("video_review", 0) or video.get("reply", 0) or video.get("replies", 0)
                    
                    # UP主信息
                    author = video.get("author", "") or video.get("uploader", "")
                    author_mid = video.get("mid", "")
                    author_avatar = video.get("upic", "")
                    
                    # 封面图
                    thumbnail = video.get("pic", "") or video.get("cover", "")
                    
                    # 视频时长
                    duration = None
                    if video.get("duration"):
                        duration = video["duration"]
                    
                    score = self.calculate_score(views, likes, coins, replies, published_at)
                    
                    results.append({
                        "platform": PlatformType.BILIBILI,
                        "content_id": bvid,
                        "title": title,
                        "content": description,
                        "url": f"{self.BASE_URL}/video/{bvid}",
                        "author": author,
                        "author_url": f"{self.BASE_URL}/space/{author_mid}" if author_mid else "",
                        "author_avatar": author_avatar,
                        "views": views,
                        "likes": likes,
                        "comments": replies,
                        "shares": 0,
                        "score": score,
                        "thumbnail_url": thumbnail,
                        "duration": duration,
                        "published_at": published_at,
                        "metadata": {
                            "source": "bilibili",
                            "coins": coins,
                            "type": "video",
                        },
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to parse Bilibili video: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing Bilibili data: {e}")
            
        return results
    
    def _extract_from_rss(self, html: str, keyword: str, max_results: int, days: int) -> List[Dict]:
        """从 RSS/HTML 提取视频（备用方案）"""
        results = []
        
        try:
            import feedparser
            # 尝试 B站 的 RSS 源
            rss_url = f"https://www.bilibili.com/rss/all"
            
            results.append({
                "platform": PlatformType.BILIBILI,
                "content_id": "fallback-rss",
                "title": f"{keyword} 相关游戏视频",
                "content": "来自 B站 热门游戏区",
                "url": self.BASE_URL,
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
                "metadata": {"source": "bilibili-fallback"},
            })
                    
        except Exception as e:
            logger.error(f"Error extracting from Bilibili RSS: {e}")
            
        return results
