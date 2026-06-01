"""Celery 定时任务 — 数据同步"""
import asyncio
import logging

from app.core.celery_app import celery_app
from app.config import settings
from app.clients.steam_client import SteamAPIClient
from app.clients.rawg_client import RAWGClient

logger = logging.getLogger(__name__)


async def _sync_steam_popular_games():
    """同步 Steam 热门游戏数据"""
    if not settings.STEAM_API_KEY:
        logger.warning("STEAM_API_KEY not set, skipping Steam sync")
        return

    from sqlalchemy import select, update
    from app.db.session import async_session
    from app.models import Game

    client = SteamAPIClient()
    apps = await client.get_app_list()

    # Process top-apps only (games with apps)
    processed = 0
    async with async_session() as db:
        for app in apps[:500]:  # Limit per sync
            try:
                details = await client.get_app_details(app["appid"])
                if not details or details.get("type") != "game":
                    continue

                existing = await db.execute(
                    select(Game).where(Game.steam_app_id == app["appid"])
                )
                game = existing.scalar_one_or_none()

                # Extract data
                genres = [g["description"] for g in details.get("genres", [])]
                tags_list = list(details.get("categories", {}).keys()) if isinstance(details.get("categories"), dict) else []
                price_data = details.get("price_overview", {})

                if game:
                    game.name = details.get("name", game.name)
                    game.description = details.get("short_description", game.description)
                    game.genres = genres
                    game.platforms = [p for p in ["windows", "mac", "linux"] if details.get(p)]
                    game.cover_image = details.get("header_image")
                    game.price = price_data.get("initial") and price_data["initial"] / 100
                    game.final_price = price_data.get("final") and price_data["final"] / 100
                    game.discount_percent = price_data.get("discount_percent", 0)
                    game.updated_at = __import__("datetime").datetime.utcnow()
                else:
                    game = Game(
                        name=details.get("name", app["name"]),
                        steam_app_id=app["appid"],
                        description=details.get("short_description"),
                        genres=genres,
                        platforms=[p for p in ["windows", "mac", "linux"] if details.get(p)],
                        developers=details.get("developers"),
                        publishers=details.get("publishers"),
                        cover_image=details.get("header_image"),
                        price=price_data.get("initial") and price_data["initial"] / 100,
                        final_price=price_data.get("final") and price_data["final"] / 100,
                        discount_percent=price_data.get("discount_percent", 0),
                        release_date=details.get("release_date", {}).get("date") and __import__("datetime").datetime.fromisoformat(details["release_date"]["date"]) if details.get("release_date", {}).get("date") else None,
                        screenshots=[s["path_full"] for s in details.get("screenshots", [])[:5]],
                    )
                    db.add(game)

                await db.commit()
                processed += 1

            except Exception as e:
                logger.error(f"Error processing app {app['appid']}: {e}")
                continue

    logger.info(f"Steam sync done: {processed} games")


async def _sync_steam_player_counts():
    """更新在线人数"""
    if not settings.STEAM_API_KEY:
        return

    from sqlalchemy import select
    from app.db.session import async_session
    from app.models import Game

    client = SteamAPIClient()
    async with async_session() as db:
        result = await db.execute(select(Game).where(Game.steam_app_id.isnot(None)).limit(100))
        games = result.scalars().all()

        for game in games:
            try:
                players = await client.get_current_players(game.steam_app_id)
                game.current_players = players
            except Exception:
                continue

        await db.commit()
    logger.info(f"Player counts updated for {len(games)} games")


async def _sync_social_content():
    """同步社交媒体内容 - 多平台聚合"""
    from sqlalchemy import select
    from app.db.session import async_session
    from app.models import Game
    from app.services.social_aggregator import SocialAggregatorService

    async with async_session() as db:
        # 获取热门游戏进行社交内容同步
        result = await db.execute(
            select(Game)
            .order_by(Game.current_players.desc().nullslast())
            .limit(20)  # 每次只同步前20个热门游戏
        )
        games = result.scalars().all()

        service = SocialAggregatorService(db)
        total_contents = 0

        for game in games:
            try:
                logger.info(f"Fetching social content for: {game.name}")
                contents = await service.fetch_and_save_game_content(game, days=7)
                total_contents += len(contents)
                logger.info(f"  Saved {len(contents)} contents for {game.name}")
            except Exception as e:
                logger.error(f"Error fetching content for {game.name}: {e}")
                continue

    logger.info(f"Social content sync done: {total_contents} total contents")


# ===== Celery Tasks =====

@celery_app.task(name="sync_steam_games")
def sync_steam_games():
    asyncio.run(_sync_steam_popular_games())


@celery_app.task(name="sync_player_counts")
def sync_player_counts():
    asyncio.run(_sync_steam_player_counts())


@celery_app.task(name="sync_social_content")
def sync_social_content():
    """定时同步社交媒体内容"""
    asyncio.run(_sync_social_content())
