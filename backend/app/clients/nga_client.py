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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        self._cookies = None

    async def _get_guest_cookies(self, client: httpx.AsyncClient):
        if self._cookies is None:
            try:
                r = await client.get(self.BASE_URL, headers=self.headers, follow_redirects=True, timeout=15)
                if r.status_code == 200:
                    self._cookies = r.cookies
                    logger.debug("NGA guest cookie obtained")
                else:
                    self._cookies = {}
            except Exception:
                self._cookies = {}

    def calculate_score(self, replies: int, views: int, published_at: Optional[datetime] = None) -> float:
        score = 0.0
        score += min(replies / 20, 15)
        score += min(views / 10000, 8)
        if published_at:
            days_since = (datetime.utcnow() - published_at).days
            score *= max(0.2, 1.0 - (days_since / 30))
        return score

    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        """搜索 NGA 游戏帖子 - 通过热门版块检索"""
        try:
            # NGA 游戏版块 fid 映射
            game_boards = {
                "7": "魔兽世界",
                "-7": "游戏综合讨论",
                "414": "艾尔登法环",
                "533": "黑神话悟空",
                "335": "原神",
                "390": "崩坏星穹铁道",
                "428": "暗黑破坏神4",
                "485": "赛博朋克2077",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                await self._get_guest_cookies(client)
                all_posts = []

                for fid in list(game_boards.keys())[:4]:
                    try:
                        url = f"{self.BASE_URL}/thread.php?fid={fid}"
                        r = await client.get(url, headers=self.headers, cookies=self._cookies, timeout=10)
                        if r.status_code == 200:
                            posts = self._parse_html(r.text, keyword, days)
                            all_posts.extend(posts)
                            logger.debug(f"NGA fid={fid}: {len(posts)} matching posts")
                    except Exception as e:
                        logger.debug(f"NGA fid={fid} error: {e}")
                        continue

                return all_posts[:max_results]
        except Exception as e:
            logger.error(f"NGA search error: {e}")
            return []

    def _parse_html(self, html: str, keyword: str, days: int) -> List[Dict]:
        results = []
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # NGA topic rows
            for row in soup.find_all("tr", class_=re.compile(r"topicrow")):
                try:
                    title_tag = row.find("a", class_=re.compile(r"topic"))
                    if not title_tag:
                        title_tag = row.find("a", class_="topic")

                    if not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)
                    if keyword.lower() not in title.lower():
                        continue

                    href = title_tag.get("href", "")
                    tid_match = re.search(r"tid=(\d+)", href)
                    tid = tid_match.group(1) if tid_match else ""

                    author_tag = row.find("a", class_="author")
                    author = author_tag.get_text(strip=True) if author_tag else ""

                    # Extract reply/view counts from td elements
                    replies = 0
                    views = 0
                    nums = []
                    for td in row.find_all("td", class_=re.compile(r"nums|cnt")):
                        text = td.get_text(strip=True)
                        n = re.findall(r"\d+", text)
                        nums.extend(int(x) for x in n)

                    if len(nums) >= 2:
                        replies, views = nums[0], nums[1]
                    elif len(nums) == 1:
                        replies = nums[0]

                    score = self.calculate_score(replies, views)

                    results.append({
                        "platform": PlatformType.NGA,
                        "content_id": tid,
                        "title": title,
                        "content": "",
                        "url": f"{self.BASE_URL}/read.php?tid={tid}" if tid else self.BASE_URL,
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
                        "published_at": None,
                        "metadata": {"source": "nga"},
                    })
                except Exception as e:
                    logger.debug(f"NGA parse row error: {e}")
                    continue
        except ImportError:
            logger.warning("BeautifulSoup not available for NGA")
        except Exception as e:
            logger.error(f"NGA parse error: {e}")
        return results
