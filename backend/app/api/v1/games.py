"""游戏 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.db.session import get_db
from app.models import Game
from app.schemas import GameOut, GameListOut

router = APIRouter()


@router.get("/", response_model=GameListOut)
async def list_games(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    total_result = await db.execute(select(func.count(Game.id)))
    total = total_result.scalar()

    result = await db.execute(
        select(Game).order_by(Game.release_date.desc().nullslast()).offset(offset).limit(page_size)
    )
    games = result.scalars().all()

    return GameListOut(
        items=[GameOut.model_validate(g) for g in games],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/upcoming", response_model=GameListOut)
async def upcoming_games(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count(Game.id)).where(
            Game.release_date > datetime.utcnow(),
            Game.release_date.isnot(None),
        )
    )
    total = count_result.scalar()

    result = await db.execute(
        select(Game)
        .where(Game.release_date > datetime.utcnow(), Game.release_date.isnot(None))
        .order_by(Game.release_date.asc())
        .offset(offset)
        .limit(page_size)
    )
    games = result.scalars().all()

    return GameListOut(
        items=[GameOut.model_validate(g) for g in games],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{game_id}", response_model=GameOut)
async def get_game(game_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="游戏不存在")
    return GameOut.model_validate(game)
