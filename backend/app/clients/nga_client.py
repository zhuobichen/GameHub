"""NGA 客户端 - 国内资深游戏论坛 (当前不可用)

NGA (bbs.nga.cn) 目前有 Cloudflare 防护，且内部 API (nuke.php)
端点已变更，旧版 action 名称全部失效。

如需重新启用，需要：
1. 使用 Playwright/Selenium 模拟真实浏览器获取 cookie
2. 逆向 NGA 前端 JS 找到新版 API 端点
3. 或等待 NGA 开放公开 API

当前返回空列表，不会阻塞 social_aggregator 流程。
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from app.models import PlatformType

logger = logging.getLogger(__name__)


class NGAClient:
    BASE_URL = "https://bbs.nga.cn"

    def __init__(self):
        pass

    def calculate_score(self, replies: int, views: int, published_at: Optional[datetime] = None) -> float:
        return 0.0

    async def search_games(self, keyword: str, max_results: int = 20, days: int = 30) -> List[Dict]:
        logger.debug(f"NGA: skipped (Cloudflare blocked, API endpoints changed)")
        return []
