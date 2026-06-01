"""用户 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import User, UserGame
from app.schemas import UserOut, UserPreferences
from app.api.deps import require_user

router = APIRouter()


@router.put("/preferences", response_model=UserOut)
async def update_preferences(
    prefs: UserPreferences,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.preferences = prefs.model_dump(exclude_none=True)
    await db.commit()
    await db.refresh(current_user)
    return UserOut.model_validate(current_user)


@router.delete("/steam")
async def unbind_steam(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.steam_id = None
    current_user.steam_api_key = None
    # remove synced games
    result = await db.execute(select(UserGame).where(UserGame.user_id == current_user.id))
    for ug in result.scalars().all():
        await db.delete(ug)
    await db.commit()
    return {"message": "Steam 解绑成功"}


@router.get("/library")
async def get_library(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserGame).where(UserGame.user_id == current_user.id)
    )
    user_games = result.scalars().all()
    return [
        {
            "game_id": ug.game_id,
            "playtime_forever": ug.playtime_forever,
            "playtime_2weeks": ug.playtime_2weeks,
            "is_wishlisted": ug.is_wishlisted,
        }
        for ug in user_games
    ]
