"""社交媒体聚合服务 - 参考 last30days-skill 的多源聚合机制"""
import asyncio
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models import Game, SocialContent, PlatformType
from app.schemas import SocialContentOut, AggregatedInsightOut
from app.clients.youtube_client import YouTubeClient
from app.clients.reddit_client import RedditClient
from app.clients.hackernews_client import HackerNewsClient
from app.clients.xiaoheihe_client import XiaoheiheClient
from app.clients.nga_client import NGAClient
from app.clients.taptap_client import TapTapClient
from app.clients.bilibili_client import BilibiliClient

logger = logging.getLogger(__name__)


class SocialAggregatorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.youtube_client = YouTubeClient()
        self.reddit_client = RedditClient()
        self.hn_client = HackerNewsClient()
        self.xiaoheihe_client = XiaoheiheClient()
        self.nga_client = NGAClient()
        self.taptap_client = TapTapClient()
        self.bilibili_client = BilibiliClient()
        
    async def fetch_and_save_game_content(
        self,
        game: Game,
        days: int = 30,
        max_per_platform: int = 20,
    ) -> List[SocialContent]:
        """
        为单个游戏获取并保存多平台社交媒体内容
        并行搜索所有平台以提高效率
        """
        queries = self._generate_search_queries(game)
        
        # 并行执行所有平台搜索
        tasks = []
        
        # YouTube 搜索
        tasks.append(self._fetch_youtube_content(queries, max_per_platform, days))
        
        # Reddit 搜索
        gaming_subreddits = ["gaming", "games", "pcgaming", "videogames"]
        if game.genres:
            genres = game.genres if isinstance(game.genres, list) else []
            gaming_subreddits.extend([g.lower() for g in genres[:3]])
        tasks.append(self._fetch_reddit_content(queries, gaming_subreddits, max_per_platform, days))
        
        # Hacker News 搜索
        tasks.append(self._fetch_hackernews_content(queries, max_per_platform, days))
        
        # 小黑盒搜索 (国内热门游戏社区)
        tasks.append(self._fetch_xiaoheihe_content(queries, max_per_platform, days))
        
        # NGA 搜索 (国内资深游戏论坛)
        tasks.append(self._fetch_nga_content(queries, max_per_platform, days))
        
        # TapTap 搜索 (国内手游社区)
        tasks.append(self._fetch_taptap_content(queries, max_per_platform, days))
        
        # B站 搜索 (国内最大视频社区)
        tasks.append(self._fetch_bilibili_content(queries, max_per_platform, days))
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并所有结果
        all_content_data = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Platform fetch error: {result}")
                continue
            all_content_data.extend(result)
            
        # 去重和保存
        saved_contents = await self._save_content_data(all_content_data, game.id)
        
        return saved_contents
        
    def _generate_search_queries(self, game: Game) -> List[str]:
        """为游戏生成多个搜索查询变体"""
        queries = [game.name]
        
        if game.name_cn:
            queries.append(game.name_cn)
            
        # 添加游戏+评论等变体
        queries.append(f"{game.name} review")
        queries.append(f"{game.name} gameplay")
        
        return list(set(queries))  # 去重
        
    async def _fetch_youtube_content(
        self,
        queries: List[str],
        max_results: int,
        days: int,
    ) -> List[Dict]:
        """获取 YouTube 内容"""
        try:
            all_videos = []
            for query in queries[:2]:  # 只查询前两个以避免过多请求
                videos = await self.youtube_client.search_videos(query, max_results // 2, days)
                all_videos.extend(videos)
            return all_videos
        except Exception as e:
            logger.error(f"YouTube fetch error: {e}")
            return []
            
    async def _fetch_reddit_content(
        self,
        queries: List[str],
        subreddits: List[str],
        max_results: int,
        days: int,
    ) -> List[Dict]:
        """获取 Reddit 内容"""
        try:
            all_posts = []
            for query in queries[:2]:
                posts = await self.reddit_client.search_posts(query, max_results // 2, days, subreddits[:5])
                all_posts.extend(posts)
            return all_posts
        except Exception as e:
            logger.error(f"Reddit fetch error: {e}")
            return []
            
    async def _fetch_hackernews_content(
        self,
        queries: List[str],
        max_results: int,
        days: int,
    ) -> List[Dict]:
        """获取 Hacker News 内容"""
        try:
            all_stories = []
            for query in queries[:1]:  # HN 限制更严格
                stories = await self.hn_client.search_stories(query, max_results, days)
                all_stories.extend(stories)
            return all_stories
        except Exception as e:
            logger.error(f"Hacker News fetch error: {e}")
            return []
            
    async def _fetch_xiaoheihe_content(
        self,
        queries: List[str],
        max_results: int,
        days: int,
    ) -> List[Dict]:
        """获取小黑盒内容 - 国内热门游戏社区"""
        try:
            all_posts = []
            for query in queries[:2]:
                # 使用游戏名称（如果有中文名称优先使用）
                search_query = query
                posts = await self.xiaoheihe_client.search_games(search_query, max_results // 2, days)
                all_posts.extend(posts)
            return all_posts
        except Exception as e:
            logger.error(f"Xiaoheihe fetch error: {e}")
            return []
            
    async def _fetch_nga_content(
        self,
        queries: List[str],
        max_results: int,
        days: int,
    ) -> List[Dict]:
        """获取 NGA 内容 - 国内资深游戏论坛"""
        try:
            all_posts = []
            for query in queries[:2]:
                posts = await self.nga_client.search_games(query, max_results // 2, days)
                all_posts.extend(posts)
            return all_posts
        except Exception as e:
            logger.error(f"NGA fetch error: {e}")
            return []
            
    async def _fetch_taptap_content(
        self,
        queries: List[str],
        max_results: int,
        days: int,
    ) -> List[Dict]:
        """获取 TapTap 内容 - 国内手游社区"""
        try:
            all_posts = []
            for query in queries[:2]:
                posts = await self.taptap_client.search_games(query, max_results // 2, days)
                all_posts.extend(posts)
            return all_posts
        except Exception as e:
            logger.error(f"TapTap fetch error: {e}")
            return []
            
    async def _fetch_bilibili_content(
        self,
        queries: List[str],
        max_results: int,
        days: int,
    ) -> List[Dict]:
        """获取 B站 内容 - 国内最大视频社区"""
        try:
            all_videos = []
            for query in queries[:2]:
                videos = await self.bilibili_client.search_games(query, max_results // 2, days)
                all_videos.extend(videos)
            return all_videos
        except Exception as e:
            logger.error(f"Bilibili fetch error: {e}")
            return []
            
    async def _save_content_data(
        self,
        content_data_list: List[Dict],
        game_id: int,
    ) -> List[SocialContent]:
        """保存内容数据到数据库"""
        saved_contents = []
        
        for content_data in content_data_list:
            # 检查是否已存在
            existing = await self.db.execute(
                select(SocialContent).where(
                    and_(
                        SocialContent.platform == content_data["platform"],
                        SocialContent.content_id == content_data["content_id"],
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue
                
            # 创建新记录
            content = SocialContent(
                game_id=game_id,
                platform=content_data["platform"],
                content_id=content_data["content_id"],
                title=content_data.get("title"),
                content=content_data.get("content"),
                url=content_data.get("url"),
                author=content_data.get("author"),
                author_url=content_data.get("author_url"),
                author_avatar=content_data.get("author_avatar"),
                views=content_data.get("views", 0),
                likes=content_data.get("likes", 0),
                comments=content_data.get("comments", 0),
                shares=content_data.get("shares", 0),
                score=content_data.get("score", 0),
                thumbnail_url=content_data.get("thumbnail_url"),
                duration=content_data.get("duration"),
                published_at=content_data.get("published_at"),
                metadata=content_data.get("metadata", {}),
            )
            
            self.db.add(content)
            saved_contents.append(content)
            
        await self.db.commit()
        return saved_contents
        
    async def get_game_insights(self, game_id: int, days: int = 30) -> AggregatedInsightOut:
        """获取游戏的聚合洞察"""
        game = await self.db.get(Game, game_id)
        if not game:
            raise ValueError("Game not found")
            
        # 获取指定时间范围内的内容
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # 获取所有相关内容
        result = await self.db.execute(
            select(SocialContent)
            .where(
                and_(
                    SocialContent.game_id == game_id,
                    SocialContent.published_at >= since_date,
                )
            )
            .order_by(SocialContent.score.desc())
            .limit(20)
        )
        top_contents = result.scalars().all()
        
        # 统计各平台分布
        platform_counts = {}
        total_mentions = 0
        for content in top_contents:
            platform = content.platform.value if hasattr(content.platform, 'value') else str(content.platform)
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
            total_mentions += 1
            
        # 计算趋势评分
        trending_score = self._calculate_trending_score(top_contents)
        
        return AggregatedInsightOut(
            game_id=game_id,
            game_name=game.name,
            total_mentions=total_mentions,
            platform_breakdown=platform_counts,
            top_posts=[SocialContentOut.model_validate(c) for c in top_contents[:10]],
            sentiment_score=None,  # 可扩展：添加情感分析
            trending_score=trending_score,
            last_updated=datetime.utcnow(),
        )
        
    def _calculate_trending_score(self, contents: List[SocialContent]) -> float:
        """计算游戏的趋势评分"""
        if not contents:
            return 0.0
            
        # 计算加权平均分
        total_score = sum(c.score for c in contents)
        avg_score = total_score / len(contents)
        
        # 计算新鲜度因子 (基于最新内容)
        if contents:
            latest = max(c.published_at for c in contents if c.published_at)
            if latest:
                days_since = (datetime.utcnow() - latest).days
                freshness_factor = max(0.1, 1.0 - (days_since / 30))
                avg_score *= freshness_factor
                
        return round(avg_score, 2)
        
    async def get_trending_games(self, limit: int = 10, days: int = 7) -> List[Tuple[Game, float]]:
        """获取趋势游戏列表"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # 查询近期有社交媒体内容的游戏
        result = await self.db.execute(
            select(
                Game,
                func.avg(SocialContent.score).label("avg_score"),
                func.count(SocialContent.id).label("content_count"),
            )
            .join(SocialContent, Game.id == SocialContent.game_id)
            .where(SocialContent.published_at >= since_date)
            .group_by(Game.id)
            .order_by(func.avg(SocialContent.score).desc())
            .limit(limit)
        )
        
        rows = result.all()
        return [(row.Game, float(row.avg_score or 0)) for row in rows]
