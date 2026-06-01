"""NGA (艾泽拉斯国家地理) 客户端 - 国内资深游戏论坛"""
import httpx
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
from app.models import PlatformType

logger = logging.getLogger(__name__)


class NGAClient:
    BASE_URL = "https://bbs.nga.cn"
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
    
    def calculate_score(self, replies: int, views: int, published_at: Optional[datetime] = None) -> float:
        """计算 NGA 内容评分 - 资深论坛权重"""
        score = 0.0
        
        # NGA 回复数权重较高
        score += min(replies / 20, 15)
        score += min(views / 10000, 8)
        
        # 时间衰减
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            decay_factor = max(0.2, 1.0 - (days_since / 30))
            score *= decay_factor
            
        return score
    
    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索 NGA 游戏相关帖子"""
        try:
            # 使用 NGA 搜索
            search_url = f"{self.BASE_URL}/thread.php"
            params = {
                "key": keyword,
                "page": 1,
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(search_url, params=params, headers=self.headers)
                if response.status_code == 200:
                    return self._parse_html_content(response.text, keyword, days)
                    
        except Exception as e:
            logger.warning(f"NGA search failed: {e}")
            return await self._fallback_search(keyword, max_results, days)
        
        return []
    
    async def _fallback_search(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """备用搜索 - 访问热门版块"""
        try:
            # 访问 NGA 热门游戏区
            hot_boards = [
                "7",   # 魔兽世界
                "335", # 原神
                "390", # 崩坏：星穹铁道
            ]
            
            all_posts = []
            for board in hot_boards[:2]:
                board_url = f"{self.BASE_URL}/thread.php?fid={board}"
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.get(board_url, headers=self.headers)
                    if response.status_code == 200:
                        posts = self._parse_html_content(response.text, keyword, days)
                        all_posts.extend(posts)
            
            return all_posts[:max_results]
                    
        except Exception as e:
            logger.error(f"NGA fallback search error: {e}")
            return []
    
    def _parse_html_content(self, html: str, keyword: str, days: int) -> List[Dict]:
        """解析 NGA HTML 内容"""
        results = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # 查找帖子列表 - NGA 的 HTML 结构较为复杂
            threads = soup.find_all("tr", class_="topicrow")
            
            for thread in threads[:30]:
                try:
                    # 提取标题
                    title_tag = thread.find("a", class_="title")
                    if not title_tag:
                        continue
                        
                    title = title_tag.get_text(strip=True)
                    if keyword.lower() not in title.lower():
                        continue
                    
                    # 提取链接
                    link = title_tag.get("href", "")
                    tid_match = re.search(r'tid=(\d+)', link)
                    tid = tid_match.group(1) if tid_match else ""
                    
                    if not tid:
                        continue
                    
                    # 提取作者
                    author_tag = thread.find("a", class_="author")
                    author = author_tag.get_text(strip=True) if author_tag else ""
                    
                    # 提取回复数和查看数
                    replies = 0
                    views = 0
                    stat_tags = thread.find_all("td")
                    for td in stat_tags:
                        text = td.get_text(strip=True)
                        if text.isdigit():
                            if replies == 0:
                                replies = int(text)
                            elif views == 0:
                                views = int(text)
                    
                    # 尝试提取时间
                    published_at = None
                    
                    score = self.calculate_score(replies, views, published_at)
                    
                    results.append({
                        "platform": PlatformType.NGA,
                        "content_id": tid,
                        "title": title,
                        "content": "",
                        "url": f"{self.BASE_URL}/read.php?tid={tid}" if tid else "",
                        "author": author,
                        "author_url": "",
                        "author_avatar": "",
                        "views": views,
                        "likes": 0,
                        "comments": replies,
                        "shares": 0,
                        "score": score,
                        "thumbnail_url": "",
                        "duration": None,
                        "published_at": published_at,
                        "metadata": {
                            "source": "nga",
                            "board": "gaming",
                        },
                    })
                    
                except Exception as e:
                    logger.debug(f"Failed to parse NGA thread: {e}")
                    continue
                    
        except ImportError:
            logger.warning("BeautifulSoup not available, skipping HTML parsing")
        except Exception as e:
            logger.error(f"Error parsing NGA HTML: {e}")
            
        return results
