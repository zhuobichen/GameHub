"""推荐 API — 基于标签的内容推荐"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models import Game, User, UserGame
from app.schemas import RecommendationOut, GameOut
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=RecommendationOut)
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tags_to_match = []
    bases = []

    if current_user:
        # Get user's top-played genres/tags from library
        result = await db.execute(
            select(UserGame).where(UserGame.user_id == current_user.id)
        )
        user_games = result.scalars().all()

        if user_games:
            game_ids = [ug.game_id for ug in user_games]
            games_result = await db.execute(select(Game).where(Game.id.in_(game_ids)))
            played_games = games_result.scalars().all()

            tag_weights = {}
            for g in played_games:
                for tag in (g.tags or []):
                    tag_weights[tag] = tag_weights.get(tag, 0) + 1
                for genre in (g.genres or []):
                    tag_weights[genre] = tag_weights.get(genre, 0) + 1

            # Top 5 tags
            sorted_tags = sorted(tag_weights.items(), key=lambda x: x[1], reverse=True)
            tags_to_match = [t for t, _ in sorted_tags[:5]]
            bases = tags_to_match

        # Also check manual preferences
        if current_user.preferences:
            for k in ("genres", "tags"):
                prefs = current_user.preferences.get(k, []) or []
                tags_to_match.extend(prefs)

    if not tags_to_match:
        # Fallback: popular games
        result = await db.execute(
            select(Game).order_by(Game.rating.desc().nullslast()).limit(limit)
        )
        games = result.scalars().all()
        return RecommendationOut(
            games=[GameOut.model_validate(g) for g in games],
            based_on=["热门评分"],
        )

    # Query games matching tags
    tags_to_match = list(set(tags_to_match))
    query = select(Game)
    if tags_to_match:
        query = query.where(Game.tags.op("?|")(tags_to_match))

    query = query.order_by(Game.rating.desc().nullslast()).limit(limit)
    result = await db.execute(query)
    games = result.scalars().all()

    return RecommendationOut(
        games=[GameOut.model_validate(g) for g in games],
        based_on=bases or ["热门"],
    )
