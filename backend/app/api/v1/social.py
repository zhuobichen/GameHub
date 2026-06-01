"""社交媒体聚合 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.db.session import get_db
from app.models import SocialContent, Game, PlatformType
from app.schemas import (
    SocialContentOut,
    SocialContentListOut,
    AggregatedInsightOut,
    GameOut,
)
from app.services.social_aggregator import SocialAggregatorService

router = APIRouter()


@router.get("/trending", response_model=List[dict])
async def get_trending_games(
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """获取趋势游戏列表"""
    service = SocialAggregatorService(db)
    trending = await service.get_trending_games(limit, days)
    
    return [
        {
            "game": GameOut.model_validate(game),
            "trending_score": score,
        }
        for game, score in trending
    ]


@router.get("/game/{game_id}/insights", response_model=AggregatedInsightOut)
async def get_game_insights(
    game_id: int,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """获取游戏的社交洞察"""
    service = SocialAggregatorService(db)
    try:
        return await service.get_game_insights(game_id, days)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/game/{game_id}/content", response_model=SocialContentListOut)
async def get_game_social_content(
    game_id: int,
    platform: Optional[PlatformType] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取游戏的社交媒体内容"""
    # 验证游戏是否存在
    game = await db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    offset = (page - 1) * page_size
    
    # 构建查询
    query = select(SocialContent).where(SocialContent.game_id == game_id)
    count_query = select(func.count(SocialContent.id)).where(SocialContent.game_id == game_id)
    
    if platform:
        query = query.where(SocialContent.platform == platform)
        count_query = count_query.where(SocialContent.platform == platform)
        
    # 执行查询
    query = query.order_by(SocialContent.score.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(query)
    contents = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return SocialContentListOut(
        items=[SocialContentOut.model_validate(c) for c in contents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/game/{game_id}/fetch", response_model=List[SocialContentOut])
async def fetch_game_social_content(
    game_id: int,
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """立即为游戏抓取社交媒体内容"""
    game = await db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
        
    service = SocialAggregatorService(db)
    contents = await service.fetch_and_save_game_content(game, days)
    
    return [SocialContentOut.model_validate(c) for c in contents]
