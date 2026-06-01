"""用户画像 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import User, UserProfile
from app.schemas import UserProfileOut, UserProfileUpdate
from app.api.deps import require_user

router = APIRouter()


@router.get("/", response_model=UserProfileOut)
async def get_profile(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="画像未生成，请先同步 Steam 库")
    return UserProfileOut.model_validate(profile)


@router.put("/", response_model=UserProfileOut)
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="画像不存在")

    if data.favorite_genres is not None:
        profile.favorite_genres = data.favorite_genres
    if data.favorite_tags is not None:
        profile.favorite_tags = data.favorite_tags
    if data.excluded_genres is not None:
        profile.excluded_genres = data.excluded_genres
    if data.notes is not None:
        profile.notes = data.notes

    await db.commit()
    await db.refresh(profile)
    return UserProfileOut.model_validate(profile)
