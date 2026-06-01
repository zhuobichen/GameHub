"""搜索 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional

from app.db.session import get_db
from app.models import Game, SearchHistory
from app.schemas import SearchParams, SearchOut, GameOut
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=SearchOut)
async def search_games(
    params: SearchParams,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = select(Game)

    # Full-text search
    if params.q:
        ts_query = " & ".join(params.q.split())
        query = query.where(
            func.to_tsvector("simple", Game.name + " " + func.coalesce(Game.name_cn, ""))
            .bool_op("@@")(
                func.plainto_tsquery("simple", params.q)
            )
        )

    # Filters
    if params.genres:
        query = query.where(Game.genres.op("?|")(params.genres))
    if params.platforms:
        query = query.where(Game.platforms.op("?|")(params.platforms))
    if params.min_price is not None:
        query = query.where(Game.final_price >= params.min_price)
    if params.max_price is not None:
        query = query.where(Game.final_price <= params.max_price)
    if params.released is not None:
        from datetime import datetime
        if params.released:
            query = query.where(Game.release_date <= datetime.utcnow())
        else:
            query = query.where(Game.release_date > datetime.utcnow())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    offset = (params.page - 1) * params.page_size
    query = query.offset(offset).limit(params.page_size)
    result = await db.execute(query)
    games = result.scalars().all()

    # Save search history
    if params.q and current_user:
        history = SearchHistory(
            user_id=current_user.id,
            query=params.q,
            result_count=total,
        )
        db.add(history)
        await db.commit()

    return SearchOut(
        items=[GameOut.model_validate(g) for g in games],
        total=total or 0,
        query=params.q,
        page=params.page,
        page_size=params.page_size,
    )
